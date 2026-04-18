using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using AutoMapper;
using MultiPageELearningApi.Data;
using MultiPageELearningApi.Dtos;

namespace MultiPageELearningApi.Controllers;

[ApiController]
[Route("api/results")]
public class ResultsController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly IMapper _mapper;

    public ResultsController(AppDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    
    [HttpGet("{userId}")]
    public async Task<IActionResult> GetResults(int userId)
    {
        if (userId <= 0)
            return BadRequest("Invalid user ID");

        var results = await _context.Results
            .Where(r => r.UserId == userId)
            .Include(r => r.Quiz)
            .OrderByDescending(r => r.AttemptDate) // 🔥 latest first
            .AsNoTracking()
            .ToListAsync();

        if (!results.Any())
            return Ok(new List<object>()); // 🔥 avoid 404

        var resultDtos = _mapper.Map<IEnumerable<ResultDto>>(results);

        return Ok(resultDtos);
    }

    
    [HttpGet("single/{id}")]
    public async Task<IActionResult> GetResult(int id)
    {
        var result = await _context.Results
            .Include(r => r.Quiz)
            .AsNoTracking()
            .FirstOrDefaultAsync(r => r.ResultId == id);

        if (result == null)
            return NotFound();

        return Ok(_mapper.Map<ResultDto>(result));
    }

    
    [HttpDelete("delete/{id}")]
    public async Task<IActionResult> DeleteResult(int id, [FromQuery] int userId)
    {
        var user = await _context.Users.FindAsync(userId);

        if (user == null || user.Role != "Admin")
            return Unauthorized("Only admin can delete results");

        var result = await _context.Results.FindAsync(id);

        if (result == null)
            return NotFound();

        _context.Results.Remove(result);
        await _context.SaveChangesAsync();

        return Ok(new { message = "Result deleted. User can reattempt." });
    }

    
    [HttpGet("all")]
    public async Task<IActionResult> GetAllResults()
    {
        var results = await _context.Results
            .Include(r => r.User)
            .Include(r => r.Quiz)
            .OrderByDescending(r => r.AttemptDate) // 🔥 latest first
            .AsNoTracking()
            .ToListAsync();

        return Ok(results.Select(r => new
        {
            r.ResultId,
            r.UserId,
            UserName = r.User != null ? r.User.FullName : "Unknown",
            r.QuizId,
            QuizName = r.Quiz != null ? r.Quiz.Title : "Unknown Quiz",
            r.Score,
            r.AttemptDate
        }));
    }

    [HttpGet("analytics")]
public async Task<IActionResult> GetAnalytics()
{
    var totalUsers = await _context.Users.CountAsync();
    var totalCourses = await _context.Courses.CountAsync();
    var totalResults = await _context.Results.CountAsync();

    var avgScore = await _context.Results
        .AverageAsync(r => (double?)r.Score) ?? 0;

    var topUsers = await _context.Results
        .Include(r => r.User)
        .GroupBy(r => r.User.FullName)
        .Select(g => new
        {
            Name = g.Key,
            AvgScore = g.Average(x => x.Score)
        })
        .OrderByDescending(x => x.AvgScore)
        .Take(5)
        .ToListAsync();

    return Ok(new
    {
        totalUsers,
        totalCourses,
        totalResults,
        averageScore = Math.Round(avgScore, 2),
        topUsers
    });
}

[HttpGet("user-analytics/{userId}")]
public async Task<IActionResult> GetUserAnalytics(int userId)
{
    var results = await _context.Results
        .Where(r => r.UserId == userId)
        .ToListAsync();

    var total = results.Count;
    var avg = results.Any() ? results.Average(r => r.Score) : 0;

    return Ok(new
    {
        totalAttempts = total,
        averageScore = Math.Round(avg, 2)
    });
}
}