using MultiPageELearningApi.Models;
using MultiPageELearningApi.Repositories;

public class UserService
{
    private readonly IGenericRepository<User> _repo;

    public UserService(IGenericRepository<User> repo)
    {
        _repo = repo;
    }

    public async Task<(bool Success, string Message, User? User)> Register(User user)
    {
        var users = await _repo.GetAllAsync();

        if (users.Any(u => u.Email == user.Email))
            return (false, "Email already exists", null);

        user.PasswordHash = BCrypt.Net.BCrypt.HashPassword(user.PasswordHash);
        user.CreatedAt = DateTime.Now;

        await _repo.AddAsync(user);
        await _repo.SaveAsync();

        return (true, "Success", user);
    }

    public async Task<User?> Login(string email, string password)
    {
        var users = await _repo.GetAllAsync();

        var user = users.FirstOrDefault(u => u.Email == email);

        if (user == null) return null;

        if (!BCrypt.Net.BCrypt.Verify(password, user.PasswordHash))
            return null;

        return user;
    }

    public async Task<User?> GetById(int id)
    {
        return await _repo.GetByIdAsync(id);
    }

    public async Task Update(User user)
    {
        _repo.Update(user);
        await _repo.SaveAsync();
    }

    public async Task Delete(User user)
    {
        _repo.Delete(user);
        await _repo.SaveAsync();
    }
}