using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using MultiPageELearningApi.Data;
using MultiPageELearningApi.Models;

namespace MultiPageELearningApi.Controllers;

[ApiController]
[Route("api/progress")]
public class ProgressController : ControllerBase
{
    private readonly AppDbContext _context;

    public ProgressController(AppDbContext context)
    {
        _context = context;
    }

    
    [HttpPost]
    public async Task<IActionResult> MarkComplete([FromQuery] int userId, [FromQuery] int courseId)
    {
        var existing = await _context.CourseProgresses
            .FirstOrDefaultAsync(x => x.UserId == userId && x.CourseId == courseId);

        if (existing == null)
        {
            _context.CourseProgresses.Add(new CourseProgress
            {
                UserId = userId,
                CourseId = courseId,
                IsCompleted = true
            });
        }
        else
        {
            existing.IsCompleted = true;
        }

        await _context.SaveChangesAsync();
        return Ok();
    }

    
    [HttpPut("undo")]
    public async Task<IActionResult> UndoCompletion([FromQuery] int userId, [FromQuery] int courseId)
    {
        var progress = await _context.CourseProgresses
            .FirstOrDefaultAsync(x => x.UserId == userId && x.CourseId == courseId);

        if (progress == null)
            return NotFound();

        progress.IsCompleted = false;

        await _context.SaveChangesAsync();
        return Ok();
    }

    
    [HttpGet("{userId}")]
    public async Task<IActionResult> GetUserProgress(int userId)
    {
        var data = await _context.CourseProgresses
            .Where(x => x.UserId == userId)
            .Include(x => x.Course)
            .ToListAsync();

        return Ok(data.Select(x => new
        {
            x.CourseId,
            x.IsCompleted,
            CourseTitle = x.Course.Title
        }));
    }

    
    [HttpGet("all")]
    public async Task<IActionResult> GetAllProgress()
    {
        var data = await _context.CourseProgresses
            .Include(x => x.User)
            .Include(x => x.Course)
            .ToListAsync();

        return Ok(data.Select(x => new
        {
            x.UserId,
            UserName = x.User.FullName,
            x.CourseId,
            CourseTitle = x.Course.Title,
            x.IsCompleted
        }));
    }
}