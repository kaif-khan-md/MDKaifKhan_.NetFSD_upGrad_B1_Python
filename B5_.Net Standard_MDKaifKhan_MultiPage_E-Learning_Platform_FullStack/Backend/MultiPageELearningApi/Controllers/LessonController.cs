using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using AutoMapper;
using MultiPageELearningApi.Models;
using MultiPageELearningApi.Dtos;
using MultiPageELearningApi.Data;
using MultiPageELearningApi.Repositories;

namespace MultiPageELearningApi.Controllers;

[ApiController]
[Route("api")]
public class LessonsController : ControllerBase
{
    private readonly IGenericRepository<Lesson> _repo;
    private readonly IMapper _mapper;
    private readonly AppDbContext _context;

    public LessonsController(
        IGenericRepository<Lesson> repo,
        IMapper mapper,
        AppDbContext context)
    {
        _repo = repo;
        _mapper = mapper;
        _context = context;
    }

    [HttpGet("courses/{courseId}/lessons")]
    public async Task<IActionResult> GetLessons(int courseId)
    {
        var lessons = (await _repo.GetAllAsync())
            .Where(l => l.CourseId == courseId)
            .OrderBy(l => l.OrderIndex);

        return Ok(_mapper.Map<IEnumerable<LessonDto>>(lessons));
    }

    
    [HttpPost("lessons")]
    public async Task<IActionResult> CreateLesson(LessonDto dto, [FromQuery] int userId)
    {
        var user = await _context.Users.FindAsync(userId);
        if (user == null || user.Role != "Admin")
            return Unauthorized("Only admin");

        var lesson = _mapper.Map<Lesson>(dto);

        var maxOrder = (await _context.Lessons
        .Where(l => l.CourseId == dto.CourseId)
        .ToListAsync())
        .Select(l => l.OrderIndex)
        .DefaultIfEmpty(0)
        .Max();

    lesson.OrderIndex = maxOrder + 1;

        await _repo.AddAsync(lesson);
        await _repo.SaveAsync();

        return Ok(_mapper.Map<LessonDto>(lesson));
    }

    [HttpPut("lessons/{id}")]
    public async Task<IActionResult> UpdateLesson(int id, LessonDto dto)
    {
        var lesson = await _repo.GetByIdAsync(id);
        if (lesson == null) return NotFound();

        _mapper.Map(dto, lesson);

        _repo.Update(lesson);
        await _repo.SaveAsync();

        return Ok(_mapper.Map<LessonDto>(lesson));
    }

    [HttpDelete("lessons/{id}")]
    public async Task<IActionResult> DeleteLesson(int id)
    {
        var lesson = await _repo.GetByIdAsync(id);
        if (lesson == null) return NotFound();

        _repo.Delete(lesson);
        await _repo.SaveAsync();

        return NoContent();
    }
}