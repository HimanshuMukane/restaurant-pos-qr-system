using Microsoft.EntityFrameworkCore;
using NodedrRestaurant.Api.Models;

namespace NodedrRestaurant.Api.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Restaurant> Restaurants => Set<Restaurant>();
    public DbSet<Branch> Branches => Set<Branch>();
    public DbSet<Role> Roles => Set<Role>();
    public DbSet<Permission> Permissions => Set<Permission>();
    public DbSet<RolePermission> RolePermissions => Set<RolePermission>();
    public DbSet<User> Users => Set<User>();
    public DbSet<License> Licenses => Set<License>();

    public DbSet<Table> Tables => Set<Table>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();
    public DbSet<Payment> Payments => Set<Payment>();

    public DbSet<MenuCategory> MenuCategories => Set<MenuCategory>();
    public DbSet<MenuItem> MenuItems => Set<MenuItem>();
    public DbSet<Ingredient> Ingredients => Set<Ingredient>();
    public DbSet<StockMovement> StockMovements => Set<StockMovement>();

    public DbSet<KitchenStation> KitchenStations => Set<KitchenStation>();
    public DbSet<Kot> Kots => Set<Kot>();
    public DbSet<KotItem> KotItems => Set<KotItem>();

    public DbSet<Expense> Expenses => Set<Expense>();
    public DbSet<CashClosing> CashClosings => Set<CashClosing>();

    public DbSet<WebhookEndpoint> WebhookEndpoints => Set<WebhookEndpoint>();
    public DbSet<IntegrationApiKey> IntegrationApiKeys => Set<IntegrationApiKey>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Exact MySQL table name mappings
        modelBuilder.Entity<Restaurant>().ToTable("restaurants");
        modelBuilder.Entity<Branch>().ToTable("branches");
        modelBuilder.Entity<Role>().ToTable("roles");
        modelBuilder.Entity<Permission>().ToTable("permissions");
        modelBuilder.Entity<RolePermission>().ToTable("role_permissions");
        modelBuilder.Entity<User>().ToTable("users");
        modelBuilder.Entity<License>().ToTable("licenses");

        modelBuilder.Entity<Table>().ToTable("tables");
        modelBuilder.Entity<Order>().ToTable("orders");
        modelBuilder.Entity<OrderItem>().ToTable("order_items");
        modelBuilder.Entity<Payment>().ToTable("payments");

        modelBuilder.Entity<MenuCategory>().ToTable("menu_categories");
        modelBuilder.Entity<MenuItem>().ToTable("menu_items");
        modelBuilder.Entity<Ingredient>().ToTable("ingredients");
        modelBuilder.Entity<StockMovement>().ToTable("stock_movements");

        modelBuilder.Entity<KitchenStation>().ToTable("kitchen_stations");
        modelBuilder.Entity<Kot>().ToTable("kots");
        modelBuilder.Entity<KotItem>().ToTable("kot_items");

        modelBuilder.Entity<Expense>().ToTable("expenses");
        modelBuilder.Entity<CashClosing>().ToTable("cash_closings");

        modelBuilder.Entity<WebhookEndpoint>().ToTable("webhook_endpoints");
        modelBuilder.Entity<IntegrationApiKey>().ToTable("integration_api_keys");

        // Relationships & Constraints
        modelBuilder.Entity<RolePermission>()
            .HasOne(rp => rp.Role)
            .WithMany(r => r.RolePermissions)
            .HasForeignKey(rp => rp.RoleId);

        modelBuilder.Entity<RolePermission>()
            .HasOne(rp => rp.Permission)
            .WithMany()
            .HasForeignKey(rp => rp.PermissionId);

        modelBuilder.Entity<User>()
            .HasOne(u => u.Role)
            .WithMany()
            .HasForeignKey(u => u.RoleId);

        modelBuilder.Entity<Order>()
            .HasOne(o => o.CreatedBy)
            .WithMany()
            .HasForeignKey(o => o.CreatedById);

        modelBuilder.Entity<Order>()
            .HasMany(o => o.Items)
            .WithOne(i => i.Order)
            .HasForeignKey(i => i.OrderId);

        modelBuilder.Entity<MenuItem>()
            .HasOne(m => m.Category)
            .WithMany(c => c.Items)
            .HasForeignKey(m => m.CategoryId);

        modelBuilder.Entity<Kot>()
            .HasMany(k => k.Items)
            .WithOne(ki => ki.Kot)
            .HasForeignKey(ki => ki.KotId);
    }
}
