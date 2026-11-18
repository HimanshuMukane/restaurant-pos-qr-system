using System;
using System.Collections.Generic;

namespace NodedrRestaurant.Api.Models;

public class KitchenStation
{
    public string Id { get; set; } = null!;
    public string BranchId { get; set; } = null!;
    public string Name { get; set; } = null!;
    public string? Description { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Branch Branch { get; set; } = null!;
}

public class Kot
{
    public string Id { get; set; } = null!;
    public string BranchId { get; set; } = null!;
    public string OrderId { get; set; } = null!;
    public string KotNumber { get; set; } = null!;
    public string Status { get; set; } = "PENDING"; // PENDING, PREPARING, READY, SERVED, CANCELLED
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public Order Order { get; set; } = null!;
    public ICollection<KotItem> Items { get; set; } = new List<KotItem>();
}

public class KotItem
{
    public string Id { get; set; } = null!;
    public string KotId { get; set; } = null!;
    public string OrderItemId { get; set; } = null!;
    public string MenuItemId { get; set; } = null!;
    public int Quantity { get; set; } = 1;
    public string Status { get; set; } = "PENDING";
    public string? Notes { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Kot Kot { get; set; } = null!;
}

public class Expense
{
    public string Id { get; set; } = null!;
    public string BranchId { get; set; } = null!;
    public string Category { get; set; } = null!;
    public decimal Amount { get; set; }
    public string? Description { get; set; }
    public string PaymentMethod { get; set; } = "CASH";
    public string CreatedById { get; set; } = null!;
    public DateTime ExpenseDate { get; set; } = DateTime.UtcNow;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Branch Branch { get; set; } = null!;
    public User CreatedBy { get; set; } = null!;
}

public class CashClosing
{
    public string Id { get; set; } = null!;
    public string BranchId { get; set; } = null!;
    public decimal OpeningFloat { get; set; }
    public decimal ExpectedCash { get; set; }
    public decimal ActualCash { get; set; }
    public decimal Difference { get; set; }
    public string? Notes { get; set; }
    public string ClosedById { get; set; } = null!;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Branch Branch { get; set; } = null!;
    public User ClosedBy { get; set; } = null!;
}

public class WebhookEndpoint
{
    public string Id { get; set; } = null!;
    public string RestaurantId { get; set; } = null!;
    public string Url { get; set; } = null!;
    public string Secret { get; set; } = null!;
    public string? Events { get; set; } // JSON
    public string? Description { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}

public class IntegrationApiKey
{
    public string Id { get; set; } = null!;
    public string RestaurantId { get; set; } = null!;
    public string Name { get; set; } = null!;
    public string KeyHash { get; set; } = null!;
    public string LastFour { get; set; } = null!;
    public string? Scopes { get; set; } // JSON
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
