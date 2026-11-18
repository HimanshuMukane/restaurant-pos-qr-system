using System;
using System.Collections.Generic;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.IdentityModel.Tokens;
using NodedrRestaurant.Api.Data;
using NodedrRestaurant.Api.Models;

var builder = WebApplication.CreateBuilder(args);

// Database configuration (MySQL 8)
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection") 
    ?? Environment.GetEnvironmentVariable("DATABASE_URL")
    ?? "Server=127.0.0.1;Port=3306;Database=nodedr_restaurant;Uid=nodedr;Pwd=nodedr_dev_pw;";

if (connectionString.StartsWith("mysql://", StringComparison.OrdinalIgnoreCase))
{
    var uri = new Uri(connectionString);
    var userInfo = uri.UserInfo.Split(':');
    connectionString = $"Server={uri.Host};Port={uri.Port};Database={uri.AbsolutePath.TrimStart('/')};Uid={userInfo[0]};Pwd={(userInfo.Length > 1 ? userInfo[1] : "")};";
}

builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseMySql(connectionString, ServerVersion.AutoDetect(connectionString)));

// Authentication & JWT
var jwtSecret = builder.Configuration["Jwt:Secret"] 
    ?? Environment.GetEnvironmentVariable("JWT_SECRET") 
    ?? "bb15a7b46296580c784c8460455c0b7e662849c5a038988a";

var key = Encoding.UTF8.GetBytes(jwtSecret);

builder.Services.AddAuthentication("SessionAuth")
    .AddJwtBearer("SessionAuth", options =>
    {
        options.RequireHttpsMetadata = false;
        options.SaveToken = true;
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(key),
            ValidateIssuer = false,
            ValidateAudience = false,
            ClockSkew = TimeSpan.Zero
        };
        options.Events = new Microsoft.AspNetCore.Authentication.JwtBearer.JwtBearerEvents
        {
            OnMessageReceived = context =>
            {
                if (context.Request.Cookies.TryGetValue("nodedr_session", out var cookieToken))
                {
                    context.Token = cookieToken;
                }
                return System.Threading.Tasks.Task.CompletedTask;
            }
        };
    });

builder.Services.AddAuthorization();

// CORS configuration (matches Next.js frontends)
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowWeb", policy =>
    {
        policy.SetIsOriginAllowed(_ => true)
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

var app = builder.Build();

app.UseCors("AllowWeb");
app.UseAuthentication();
app.UseAuthorization();

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------
app.MapGet("/health", () => Results.Ok(new 
{ 
    status = "ok", 
    framework = "ASP.NET Core (.NET 9)", 
    orm = "EF Core 9", 
    db = "MySQL 8" 
}));

// ---------------------------------------------------------------------------
// Auth Endpoints
// ---------------------------------------------------------------------------
app.MapPost("/api/v1/auth/login", async (AppDbContext db, HttpContext http, LoginRequest req) =>
{
    if (string.IsNullOrWhiteSpace(req.Email) || string.IsNullOrWhiteSpace(req.Password))
        return Results.BadRequest(new { message = "Email and password are required" });

    var user = await db.Users.Include(u => u.Role).FirstOrDefaultAsync(u => u.Email == req.Email);
    if (user == null || !user.IsActive)
        return Results.Unauthorized();

    if (!BCrypt.Net.BCrypt.Verify(req.Password, user.PasswordHash))
        return Results.Unauthorized();

    var token = GenerateJwtToken(user, key);

    http.Response.Cookies.Append("nodedr_session", token, new CookieOptions
    {
        HttpOnly = true,
        Secure = false,
        SameSite = SameSiteMode.Lax,
        Expires = DateTimeOffset.UtcNow.AddHours(12),
        Path = "/"
    });

    return Results.Ok(new
    {
        token,
        user = new
        {
            id = user.Id,
            email = user.Email,
            name = user.Name,
            restaurantId = user.RestaurantId,
            role = user.Role?.Name ?? "Staff"
        }
    });
});

app.MapPost("/api/v1/auth/pin-login", async (AppDbContext db, HttpContext http, PinLoginRequest req) =>
{
    if (string.IsNullOrWhiteSpace(req.Pin))
        return Results.BadRequest(new { message = "PIN is required" });

    var users = await db.Users.Include(u => u.Role).Where(u => u.IsActive && u.PinHash != null).ToListAsync();
    User? authenticatedUser = null;

    foreach (var u in users)
    {
        if (u.PinHash == req.Pin || BCrypt.Net.BCrypt.Verify(req.Pin, u.PinHash))
        {
            authenticatedUser = u;
            break;
        }
    }

    if (authenticatedUser == null)
        return Results.Unauthorized();

    var token = GenerateJwtToken(authenticatedUser, key);

    http.Response.Cookies.Append("nodedr_session", token, new CookieOptions
    {
        HttpOnly = true,
        Secure = false,
        SameSite = SameSiteMode.Lax,
        Expires = DateTimeOffset.UtcNow.AddHours(12),
        Path = "/"
    });

    return Results.Ok(new
    {
        token,
        user = new
        {
            id = authenticatedUser.Id,
            email = authenticatedUser.Email,
            name = authenticatedUser.Name,
            restaurantId = authenticatedUser.RestaurantId,
            role = authenticatedUser.Role?.Name ?? "Staff"
        }
    });
});

app.MapPost("/api/v1/auth/logout", (HttpContext http) =>
{
    http.Response.Cookies.Delete("nodedr_session", new CookieOptions { Path = "/" });
    return Results.Ok(new { message = "Logged out successfully" });
});

app.MapGet("/api/v1/me", async (AppDbContext db, HttpContext http) =>
{
    var userId = http.User.FindFirstValue(ClaimTypes.NameIdentifier);
    if (string.IsNullOrEmpty(userId))
        return Results.Unauthorized();

    var user = await db.Users.Include(u => u.Role).FirstOrDefaultAsync(u => u.Id == userId);
    if (user == null)
        return Results.Unauthorized();

    var license = await db.Licenses.FirstOrDefaultAsync(l => l.RestaurantId == user.RestaurantId);

    return Results.Ok(new
    {
        id = user.Id,
        email = user.Email,
        name = user.Name,
        restaurantId = user.RestaurantId,
        role = user.Role?.Name ?? "Staff",
        license = license != null ? new { status = license.Status, validUntil = license.ValidUntil } : null
    });
}).RequireAuthorization();

// ---------------------------------------------------------------------------
// POS & Orders Endpoints
// ---------------------------------------------------------------------------
app.MapGet("/api/v1/orders", async (AppDbContext db, HttpContext http, string? branchId, string? status) =>
{
    var branch = http.Request.Headers["x-branch-id"].ToString();
    if (string.IsNullOrEmpty(branch)) branch = branchId;

    var query = db.Orders.Include(o => o.Items).Include(o => o.CreatedBy).AsQueryable();

    if (!string.IsNullOrEmpty(branch))
        query = query.Where(o => o.BranchId == branch);

    if (!string.IsNullOrEmpty(status))
        query = query.Where(o => o.Status == status);

    var orders = await query.OrderByDescending(o => o.CreatedAt).Take(50).ToListAsync();
    return Results.Ok(new { data = orders });
}).RequireAuthorization();

app.MapPost("/api/v1/orders", async (AppDbContext db, HttpContext http, CreateOrderRequest req) =>
{
    var userId = http.User.FindFirstValue(ClaimTypes.NameIdentifier) ?? "system";
    if (string.IsNullOrEmpty(req.BranchId) || req.Items == null || req.Items.Count == 0)
        return Results.BadRequest(new { message = "BranchId and items are required" });

    decimal subtotal = 0;
    var orderItems = new List<OrderItem>();

    foreach (var it in req.Items)
    {
        var lineTotal = it.UnitPrice * it.Quantity;
        subtotal += lineTotal;
        orderItems.Add(new OrderItem
        {
            Id = $"item_{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}_{Guid.NewGuid().ToString("N")[..5]}",
            MenuItemId = it.MenuItemId,
            Quantity = it.Quantity,
            UnitPrice = it.UnitPrice,
            TotalPrice = lineTotal,
            Status = "PENDING"
        });
    }

    var taxAmount = Math.Round(subtotal * 0.05m, 2);
    var totalAmount = subtotal + taxAmount;
    var orderNumber = $"{DateTime.UtcNow:yyyyMMdd}-{Random.Shared.Next(1000, 9999)}";

    var order = new Order
    {
        Id = $"ord_{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}_{Guid.NewGuid().ToString("N")[..5]}",
        BranchId = req.BranchId,
        TableId = req.TableId,
        OrderNumber = orderNumber,
        Type = req.Type ?? "DINE_IN",
        Status = "OPEN",
        CreatedById = userId,
        Subtotal = subtotal,
        DiscountAmount = 0,
        TaxAmount = taxAmount,
        TotalAmount = totalAmount,
        GuestName = req.GuestName,
        Items = orderItems
    };

    db.Orders.Add(order);

    if (!string.IsNullOrEmpty(req.TableId))
    {
        var table = await db.Tables.FindAsync(req.TableId);
        if (table != null) table.Status = "OCCUPIED";
    }

    await db.SaveChangesAsync();
    return Results.Created($"/api/v1/orders/{order.Id}", new { data = order });
}).RequireAuthorization();

app.MapGet("/api/v1/orders/{id}", async (AppDbContext db, string id) =>
{
    var order = await db.Orders.Include(o => o.Items).Include(o => o.CreatedBy).FirstOrDefaultAsync(o => o.Id == id);
    return order != null ? Results.Ok(new { data = order }) : Results.NotFound(new { message = "Order not found" });
}).RequireAuthorization();

app.MapPatch("/api/v1/orders/{id}/status", async (AppDbContext db, string id, UpdateStatusRequest req) =>
{
    var order = await db.Orders.FindAsync(id);
    if (order == null) return Results.NotFound(new { message = "Order not found" });

    order.Status = req.Status;
    order.UpdatedAt = DateTime.UtcNow;
    await db.SaveChangesAsync();

    return Results.Ok(new { data = order });
}).RequireAuthorization();

// ---------------------------------------------------------------------------
// Tables Endpoints
// ---------------------------------------------------------------------------
app.MapGet("/api/v1/tables", async (AppDbContext db, HttpContext http, string? branchId) =>
{
    var branch = http.Request.Headers["x-branch-id"].ToString();
    if (string.IsNullOrEmpty(branch)) branch = branchId;

    var query = db.Tables.AsQueryable();
    if (!string.IsNullOrEmpty(branch))
        query = query.Where(t => t.BranchId == branch);

    var tables = await query.OrderBy(t => t.Name).ToListAsync();
    return Results.Ok(new { data = tables });
}).RequireAuthorization();

app.MapPatch("/api/v1/tables/{id}/status", async (AppDbContext db, string id, UpdateStatusRequest req) =>
{
    var table = await db.Tables.FindAsync(id);
    if (table == null) return Results.NotFound(new { message = "Table not found" });

    table.Status = req.Status;
    table.UpdatedAt = DateTime.UtcNow;
    await db.SaveChangesAsync();

    return Results.Ok(new { data = table });
}).RequireAuthorization();

// ---------------------------------------------------------------------------
// Menu & Catalog Endpoints
// ---------------------------------------------------------------------------
app.MapGet("/api/v1/menu", async (AppDbContext db, string? restaurantId) =>
{
    var query = db.MenuCategories.Include(c => c.Items.Where(i => i.IsAvailable)).Where(c => c.IsActive).AsQueryable();
    if (!string.IsNullOrEmpty(restaurantId))
        query = query.Where(c => c.RestaurantId == restaurantId);

    var categories = await query.OrderBy(c => c.DisplayOrder).ToListAsync();
    return Results.Ok(new { data = categories });
});

// ---------------------------------------------------------------------------
// Inventory & Stock Endpoints
// ---------------------------------------------------------------------------
app.MapGet("/api/v1/inventory", async (AppDbContext db, HttpContext http, string? branchId) =>
{
    var branch = http.Request.Headers["x-branch-id"].ToString();
    if (string.IsNullOrEmpty(branch)) branch = branchId;

    var query = db.Ingredients.AsQueryable();
    if (!string.IsNullOrEmpty(branch))
        query = query.Where(i => i.BranchId == branch);

    var items = await query.OrderBy(i => i.Name).ToListAsync();
    return Results.Ok(new { data = items });
}).RequireAuthorization();

// ---------------------------------------------------------------------------
// Kitchen (KDS) & KOTs Endpoints
// ---------------------------------------------------------------------------
app.MapGet("/api/v1/kitchen/tickets", async (AppDbContext db, HttpContext http, string? branchId) =>
{
    var branch = http.Request.Headers["x-branch-id"].ToString();
    if (string.IsNullOrEmpty(branch)) branch = branchId;

    var query = db.Kots.Include(k => k.Items).Include(k => k.Order).AsQueryable();
    if (!string.IsNullOrEmpty(branch))
        query = query.Where(k => k.BranchId == branch);

    var tickets = await query.Where(k => k.Status == "PENDING" || k.Status == "PREPARING")
                             .OrderBy(k => k.CreatedAt)
                             .ToListAsync();

    return Results.Ok(new { data = tickets });
}).RequireAuthorization();

app.MapPatch("/api/v1/kitchen/tickets/{id}/status", async (AppDbContext db, string id, UpdateStatusRequest req) =>
{
    var kot = await db.Kots.FindAsync(id);
    if (kot == null) return Results.NotFound(new { message = "KOT not found" });

    kot.Status = req.Status;
    kot.UpdatedAt = DateTime.UtcNow;
    await db.SaveChangesAsync();

    return Results.Ok(new { data = kot });
}).RequireAuthorization();

// ---------------------------------------------------------------------------
// Accounting & Cash Drawer Endpoints
// ---------------------------------------------------------------------------
app.MapGet("/api/v1/accounting/expenses", async (AppDbContext db, HttpContext http, string? branchId) =>
{
    var branch = http.Request.Headers["x-branch-id"].ToString();
    if (string.IsNullOrEmpty(branch)) branch = branchId;

    var query = db.Expenses.Include(e => e.CreatedBy).AsQueryable();
    if (!string.IsNullOrEmpty(branch))
        query = query.Where(e => e.BranchId == branch);

    var expenses = await query.OrderByDescending(e => e.ExpenseDate).Take(100).ToListAsync();
    return Results.Ok(new { data = expenses });
}).RequireAuthorization();

app.MapPost("/api/v1/accounting/expenses", async (AppDbContext db, HttpContext http, CreateExpenseRequest req) =>
{
    var userId = http.User.FindFirstValue(ClaimTypes.NameIdentifier) ?? "system";
    if (string.IsNullOrEmpty(req.BranchId) || string.IsNullOrEmpty(req.Category))
        return Results.BadRequest(new { message = "BranchId and category are required" });

    var expense = new Expense
    {
        Id = $"exp_{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}_{Guid.NewGuid().ToString("N")[..5]}",
        BranchId = req.BranchId,
        Category = req.Category,
        Amount = req.Amount,
        Description = req.Description,
        PaymentMethod = req.PaymentMethod ?? "CASH",
        CreatedById = userId,
        ExpenseDate = req.ExpenseDate ?? DateTime.UtcNow
    };

    db.Expenses.Add(expense);
    await db.SaveChangesAsync();

    return Results.Created($"/api/v1/accounting/expenses/{expense.Id}", new { data = expense });
}).RequireAuthorization();

// ---------------------------------------------------------------------------
// Webhooks & Integrations Endpoints
// ---------------------------------------------------------------------------
app.MapGet("/api/v1/integrations/webhooks", async (AppDbContext db) =>
{
    var webhooks = await db.WebhookEndpoints.OrderByDescending(w => w.CreatedAt).ToListAsync();
    return Results.Ok(new { data = webhooks });
}).RequireAuthorization();

app.MapPost("/api/v1/integrations/api-keys", async (AppDbContext db, HttpContext http, CreateApiKeyRequest req) =>
{
    if (string.IsNullOrWhiteSpace(req.Name))
        return Results.BadRequest(new { message = "Name is required" });

    var rawKey = $"ordr_ext_{Convert.ToHexString(RandomNumberGenerator.GetBytes(24)).ToLower()}";
    var lastFour = rawKey[^4..];
    var keyHash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(rawKey))).ToLower();

    var apiKey = new IntegrationApiKey
    {
        Id = $"key_{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}_{Guid.NewGuid().ToString("N")[..5]}",
        RestaurantId = req.RestaurantId ?? "demo-restaurant",
        Name = req.Name,
        KeyHash = keyHash,
        LastFour = lastFour,
        Scopes = "[\"orders:read\", \"orders:write\"]",
        IsActive = true
    };

    db.IntegrationApiKeys.Add(apiKey);
    await db.SaveChangesAsync();

    return Results.Created($"/api/v1/integrations/api-keys/{apiKey.Id}", new
    {
        data = new
        {
            id = apiKey.Id,
            name = apiKey.Name,
            apiKey = rawKey,
            lastFour,
            scopes = apiKey.Scopes
        }
    });
}).RequireAuthorization();

app.Run();

// ---------------------------------------------------------------------------
// Helper Methods & Request DTOs
// ---------------------------------------------------------------------------
static string GenerateJwtToken(User user, byte[] key)
{
    var tokenHandler = new JwtSecurityTokenHandler();
    var tokenDescriptor = new SecurityTokenDescriptor
    {
        Subject = new ClaimsIdentity(new[]
        {
            new Claim(ClaimTypes.NameIdentifier, user.Id),
            new Claim(ClaimTypes.Email, user.Email),
            new Claim(ClaimTypes.Role, user.Role?.Name ?? "Staff"),
            new Claim("restaurantId", user.RestaurantId)
        }),
        Expires = DateTime.UtcNow.AddHours(12),
        SigningCredentials = new SigningCredentials(new SymmetricSecurityKey(key), SecurityAlgorithms.HmacSha256Signature)
    };
    var token = tokenHandler.CreateToken(tokenDescriptor);
    return tokenHandler.WriteToken(token);
}

public record LoginRequest(string Email, string Password);
public record PinLoginRequest(string Pin);
public record UpdateStatusRequest(string Status);
public record CreateOrderItemRequest(string MenuItemId, int Quantity, decimal UnitPrice);
public record CreateOrderRequest(string BranchId, string? TableId, string? Type, string? GuestName, List<CreateOrderItemRequest> Items);
public record CreateExpenseRequest(string BranchId, string Category, decimal Amount, string? Description, string? PaymentMethod, DateTime? ExpenseDate);
public record CreateApiKeyRequest(string Name, string? RestaurantId);
