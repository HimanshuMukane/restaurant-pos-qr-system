using System;
using System.Collections.Generic;

namespace NodedrRestaurant.Api.Models;

public class MenuCategory
{
    public string Id { get; set; } = null!;
    public string RestaurantId { get; set; } = null!;
    public string Name { get; set; } = null!;
    public string? Description { get; set; }
    public int DisplayOrder { get; set; } = 0;
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<MenuItem> Items { get; set; } = new List<MenuItem>();
}

public class MenuItem
{
    public string Id { get; set; } = null!;
    public string RestaurantId { get; set; } = null!;
    public string CategoryId { get; set; } = null!;
    public string Name { get; set; } = null!;
    public string? Description { get; set; }
    public decimal Price { get; set; }
    public decimal? HalfPrice { get; set; }
    public string? ImageUrl { get; set; }
    public bool IsVeg { get; set; } = true;
    public bool IsAvailable { get; set; } = true;
    public string SpiceLevel { get; set; } = "NONE";
    public string? Allergens { get; set; } // JSON
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public MenuCategory Category { get; set; } = null!;
}

public class Ingredient
{
    public string Id { get; set; } = null!;
    public string BranchId { get; set; } = null!;
    public string Name { get; set; } = null!;
    public string Unit { get; set; } = "KG";
    public string Kind { get; set; } = "PURCHASED";
    public decimal CurrentStock { get; set; } = 0;
    public decimal ReorderLevel { get; set; } = 0;
    public decimal CostPerUnit { get; set; } = 0;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public Branch Branch { get; set; } = null!;
    public ICollection<StockMovement> StockMovements { get; set; } = new List<StockMovement>();
}

public class StockMovement
{
    public string Id { get; set; } = null!;
    public string IngredientId { get; set; } = null!;
    public string Type { get; set; } = "USAGE"; // PURCHASE, USAGE, WASTE, ADJUSTMENT
    public decimal Quantity { get; set; }
    public decimal UnitCost { get; set; }
    public string? Reason { get; set; }
    public string CreatedById { get; set; } = null!;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Ingredient Ingredient { get; set; } = null!;
}
