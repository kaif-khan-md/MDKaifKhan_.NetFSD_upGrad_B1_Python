using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using AutoMapper;
using MultiPageELearningApi.Data;
using MultiPageELearningApi.Dtos;

namespace MultiPageELearningApi.Controllers;

[ApiController]
[Route("api/analytics")]
public class AnalyticsController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly IMapper _mapper;

    public AnalyticsController(AppDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    // WHERE
    [HttpGet("courses-by-user/{userId}")]
    public async Task<IActionResult> GetCoursesByUser(int userId)
    {
        var courses = await _context.Courses
            .Where(c => c.CreatedBy == userId)
            .AsNoTracking()
            .ToListAsync();

        var result = _mapper.Map<IEnumerable<CourseDto>>(courses);

        return Ok(result);
    }

    //  ORDER BY
    [HttpGet("courses-sorted")]
    public async Task<IActionResult> GetSortedCourses()
    {
        var courses = await _context.Courses
            .OrderByDescending(c => c.CreatedAt)
            .AsNoTracking()
            .ToListAsync();

        var result = _mapper.Map<IEnumerable<CourseDto>>(courses);

        return Ok(result);
    }

    //  JOIN (Course + Lessons)
    [HttpGet("courses-with-lessons")]
    public async Task<IActionResult> GetCoursesWithLessons()
    {
        var courses = await _context.Courses
            .Include(c => c.Lessons)
            .AsNoTracking()
            .ToListAsync();

        // Optional: return only course DTO (lessons ignored)
        var result = _mapper.Map<IEnumerable<CourseDto>>(courses);

        return Ok(result);
    }

    //  GROUP BY + COUNT + AVG
    [HttpGet("user-performance")]
    public async Task<IActionResult> GetUserPerformance()
    {
        var stats = await _context.Results
            .GroupBy(r => r.UserId)
            .Select(g => new
            {
                UserId = g.Key,
                TotalAttempts = g.Count(),
                AverageScore = g.Average(r => r.Score)
            })
            .ToListAsync();

        return Ok(stats);
    }

    // SUBQUERY
    [HttpGet("above-average")]
public async Task<IActionResult> GetAboveAverageUsers()
{
    if (!_context.Results.Any())
        return Ok(new List<object>()); // 🔥 FIX: no crash

    var avgScore = await _context.Results.AverageAsync(r => r.Score);

    var users = await _context.Results
        .Where(r => r.Score > avgScore)
        .Select(r => new
        {
            r.UserId,
            r.Score
        })
        .ToListAsync();

    return Ok(users);
}

    //  UNION
    [HttpGet("combined-results")]
    public async Task<IActionResult> GetCombinedResults()
    {
        var quiz1 = _context.Results
            .Where(r => r.QuizId == 1)
            .Select(r => new { r.UserId, r.Score });

        var quiz2 = _context.Results
            .Where(r => r.QuizId == 2)
            .Select(r => new { r.UserId, r.Score });

        var combined = await quiz1.Union(quiz2).ToListAsync();

        return Ok(combined);
    }
}