using System;
using System.Collections.Generic;

namespace NodedrRestaurant.Api.Models;

public class Table
{
    public string Id { get; set; } = null!;
    public string BranchId { get; set; } = null!;
    public string Name { get; set; } = null!;
    public int Capacity { get; set; } = 4;
    public string Status { get; set; } = "AVAILABLE"; // AVAILABLE, OCCUPIED, RESERVED, CLEANING
    public string? QrCode { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public Branch Branch { get; set; } = null!;
}

public class Order
{
    public string Id { get; set; } = null!;
    public string BranchId { get; set; } = null!;
    public string OrderNumber { get; set; } = null!;
    public string Type { get; set; } = "DINE_IN"; // DINE_IN, TAKEAWAY, DELIVERY
    public string Status { get; set; } = "OPEN"; // OPEN, IN_KITCHEN, READY, SERVED, COMPLETED, CANCELLED
    public string? TableId { get; set; }
    public string CreatedById { get; set; } = null!;
    public decimal Subtotal { get; set; }
    public decimal DiscountAmount { get; set; }
    public decimal TaxAmount { get; set; }
    public decimal TotalAmount { get; set; }
    public string? GuestName { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public Branch Branch { get; set; } = null!;
    public User CreatedBy { get; set; } = null!;
    public ICollection<OrderItem> Items { get; set; } = new List<OrderItem>();
    public ICollection<Payment> Payments { get; set; } = new List<Payment>();
}

public class OrderItem
{
    public string Id { get; set; } = null!;
    public string OrderId { get; set; } = null!;
    public string MenuItemId { get; set; } = null!;
    public int Quantity { get; set; } = 1;
    public decimal UnitPrice { get; set; }
    public decimal TotalPrice { get; set; }
    public string Status { get; set; } = "PENDING";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public Order Order { get; set; } = null!;
}

public class Payment
{
    public string Id { get; set; } = null!;
    public string OrderId { get; set; } = null!;
    public decimal Amount { get; set; }
    public string Method { get; set; } = "CASH"; // CASH, CARD, UPI, OTHER
    public string Status { get; set; } = "COMPLETED";
    public string CreatedById { get; set; } = null!;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Order Order { get; set; } = null!;
}
