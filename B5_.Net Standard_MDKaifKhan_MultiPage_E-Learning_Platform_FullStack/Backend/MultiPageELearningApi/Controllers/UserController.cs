using Microsoft.AspNetCore.Mvc;
using AutoMapper;
using MultiPageELearningApi.Models;
using MultiPageELearningApi.Dtos;
using MultiPageELearningApi.Repositories;

namespace MultiPageELearningApi.Controllers;

[ApiController]
[Route("api/users")]
public class UsersController : ControllerBase
{
    private readonly IGenericRepository<User> _repo;

    public UsersController(IGenericRepository<User> repo)
    {
        _repo = repo;
    }

    [HttpPost("register")]
    public async Task<IActionResult> Register(RegisterUserDto dto)
    {
        if (!ModelState.IsValid)
        return BadRequest(ModelState);
        
        var users = await _repo.GetAllAsync();

        if (users.Any(u => u.Email == dto.Email))
            return BadRequest("Email already exists");

        var user = new User
        {
            FullName = dto.FullName,
            Email = dto.Email,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(dto.Password),
            Role = "User",
            CreatedAt = DateTime.Now
        };

        await _repo.AddAsync(user);
        await _repo.SaveAsync();

        return Ok(new
        {
            user.UserId,
            user.FullName,
            user.Email,
            user.Role
        });
    }

    [HttpPost("register-admin")]
    public async Task<IActionResult> RegisterAdmin(RegisterUserDto dto)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);
        var user = new User
        {
            FullName = dto.FullName,
            Email = dto.Email,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(dto.Password),
            Role = "Admin",
            CreatedAt = DateTime.Now
        };

        await _repo.AddAsync(user);
        await _repo.SaveAsync();

        return Ok("Admin created");
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login(LoginDto dto)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);
        var users = await _repo.GetAllAsync();

        var user = (await _repo.GetAllAsync())
            .FirstOrDefault(u => u.Email == dto.Email);

        if (user == null || !BCrypt.Net.BCrypt.Verify(dto.Password, user.PasswordHash))
            return Unauthorized("Invalid credentials");

        return Ok(new
        {
            user.UserId,
            user.FullName,
            user.Email,
            user.Role
        });
    }

    
    [HttpGet("{id}")]
    public async Task<IActionResult> GetUser(int id)
    {
        var user = await _repo.GetByIdAsync(id);
        if (user == null) return NotFound();

        return Ok(new { user.UserId, user.FullName, user.Email });
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> UpdateUser(int id, UserDto dto)
    {
        var user = await _repo.GetByIdAsync(id);
        if (user == null) return NotFound();

        user.FullName = dto.FullName;
        user.Email = dto.Email;

        _repo.Update(user);
        await _repo.SaveAsync();

        return Ok("Updated");
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> DeleteUser(int id)
    {
        var user = await _repo.GetByIdAsync(id);
        if (user == null) return NotFound();

        _repo.Delete(user);
        await _repo.SaveAsync();

        return NoContent();
    }
}