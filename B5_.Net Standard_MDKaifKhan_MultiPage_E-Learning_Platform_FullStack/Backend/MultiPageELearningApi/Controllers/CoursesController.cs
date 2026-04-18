using Microsoft.AspNetCore.Mvc;
using AutoMapper;
using MultiPageELearningApi.Models;
using MultiPageELearningApi.Dtos;
using MultiPageELearningApi.Data;
using MultiPageELearningApi.Repositories;

namespace MultiPageELearningApi.Controllers;

[ApiController]
[Route("api/courses")]
public class CoursesController : ControllerBase
{
    private readonly IGenericRepository<Course> _repo;
    private readonly IMapper _mapper;
    private readonly AppDbContext _context;

    public CoursesController(
        IGenericRepository<Course> repo,
        IMapper mapper,
        AppDbContext context)
    {
        _repo = repo;
        _mapper = mapper;
        _context = context;
    }

    [HttpGet]
    public async Task<IActionResult> GetCourses()
    {
        var courses = await _repo.GetAllAsync();
        return Ok(_mapper.Map<IEnumerable<CourseDto>>(courses));
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetCourse(int id)
    {
        var course = await _repo.GetByIdAsync(id);
        if (course == null) return NotFound();

        return Ok(_mapper.Map<CourseDto>(course));
    }

    
    [HttpPost]
    public async Task<IActionResult> CreateCourse(CreateCourseDto dto)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        var user = await _context.Users.FindAsync(dto.CreatedBy);
        if (user == null || user.Role != "Admin")
            return Unauthorized("Only admin");

        var course = _mapper.Map<Course>(dto);
        course.CreatedAt = DateTime.Now;

        await _repo.AddAsync(course);
        await _repo.SaveAsync();

        return Ok(_mapper.Map<CourseDto>(course));
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> UpdateCourse(int id, CreateCourseDto dto)
    {
        var course = await _repo.GetByIdAsync(id);
        if (course == null) return NotFound();

        var user = await _context.Users.FindAsync(dto.CreatedBy);
        if (user == null || user.Role != "Admin")
            return Unauthorized("Only admin");

        _mapper.Map(dto, course);

        _repo.Update(course);
        await _repo.SaveAsync();

        return Ok(_mapper.Map<CourseDto>(course));
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> DeleteCourse(int id)
    {
        var course = await _repo.GetByIdAsync(id);
        if (course == null) return NotFound();

        _repo.Delete(course);
        await _repo.SaveAsync();

        return NoContent();
    }
}