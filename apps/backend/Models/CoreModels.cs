using System;
using System.Collections.Generic;

namespace NodedrRestaurant.Api.Models;

public class Restaurant
{
    public string Id { get; set; } = null!;
    public string Name { get; set; } = null!;
    public string Slug { get; set; } = null!;
    public string Currency { get; set; } = "INR";
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<Branch> Branches { get; set; } = new List<Branch>();
    public ICollection<User> Users { get; set; } = new List<User>();
    public License? License { get; set; }
}

public class Branch
{
    public string Id { get; set; } = null!;
    public string RestaurantId { get; set; } = null!;
    public string Name { get; set; } = null!;
    public string? Address { get; set; }
    public string? Phone { get; set; }
    public bool IsMain { get; set; } = true;
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public Restaurant Restaurant { get; set; } = null!;
    public ICollection<Table> Tables { get; set; } = new List<Table>();
    public ICollection<Order> Orders { get; set; } = new List<Order>();
}

public class Role
{
    public string Id { get; set; } = null!;
    public string RestaurantId { get; set; } = null!;
    public string Name { get; set; } = null!;
    public bool IsSystem { get; set; } = false;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<RolePermission> RolePermissions { get; set; } = new List<RolePermission>();
}

public class Permission
{
    public string Id { get; set; } = null!;
    public string Key { get; set; } = null!;
    public string? Description { get; set; }
    public string Category { get; set; } = "GENERAL";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

public class RolePermission
{
    public string Id { get; set; } = null!;
    public string RoleId { get; set; } = null!;
    public string PermissionId { get; set; } = null!;

    public Role Role { get; set; } = null!;
    public Permission Permission { get; set; } = null!;
}

public class User
{
    public string Id { get; set; } = null!;
    public string RestaurantId { get; set; } = null!;
    public string RoleId { get; set; } = null!;
    public string Name { get; set; } = null!;
    public string Email { get; set; } = null!;
    public string? Phone { get; set; }
    public string PasswordHash { get; set; } = null!;
    public string? PinHash { get; set; }
    public bool IsActive { get; set; } = true;
    public bool IsSuperAdmin { get; set; } = false;
    public DateTime? SessionsValidFrom { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public Restaurant Restaurant { get; set; } = null!;
    public Role Role { get; set; } = null!;
}

public class License
{
    public string Id { get; set; } = null!;
    public string RestaurantId { get; set; } = null!;
    public string Status { get; set; } = "ACTIVE";
    public DateTime ValidFrom { get; set; }
    public DateTime ValidUntil { get; set; }
    public int GracePeriodDays { get; set; } = 3;
    public int MaxBranches { get; set; } = 1;
    public int MaxUsers { get; set; } = 10;
    public string? EnabledModules { get; set; } // JSON in MySQL
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public Restaurant Restaurant { get; set; } = null!;
}
