using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using AutoMapper;
using MultiPageELearningApi.Models;
using MultiPageELearningApi.Data;
using MultiPageELearningApi.Dtos;

namespace MultiPageELearningApi.Controllers;

[ApiController]
[Route("api")]
public class QuizController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly IMapper _mapper;

    public QuizController(AppDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }


    [HttpGet("quizzes/{courseId}")]
    public async Task<IActionResult> GetQuizzes(int courseId)
    {
        var quizzes = await _context.Quizzes
            .Where(q => q.CourseId == courseId)
            .AsNoTracking()
            .ToListAsync();

        return Ok(_mapper.Map<IEnumerable<QuizDto>>(quizzes));
    }

    
    [HttpGet("quizzes/{quizId}/questions")]
    public async Task<IActionResult> GetQuestions(int quizId)
    {
        var questions = await _context.Questions
            .Where(q => q.QuizId == quizId)
            .AsNoTracking()
            .ToListAsync();

        return Ok(_mapper.Map<IEnumerable<QuestionDto>>(questions));
    }

    
    [HttpPost("quizzes")]
    public async Task<IActionResult> CreateQuiz(QuizDto dto, [FromQuery] int userId)
    {
        var user = await _context.Users.FindAsync(userId);
        if (user == null || user.Role != "Admin")
            return Unauthorized("Only admin");

        var quiz = _mapper.Map<Quiz>(dto);

        _context.Quizzes.Add(quiz);
        await _context.SaveChangesAsync();

        return Ok(_mapper.Map<QuizDto>(quiz));
    }

    [HttpPost("questions")]
    public async Task<IActionResult> CreateQuestion(QuestionDto dto, [FromQuery] int userId)
    {
        var user = await _context.Users.FindAsync(userId);
        if (user == null || user.Role != "Admin")
            return Unauthorized("Only admin");

        var question = _mapper.Map<Question>(dto);

        _context.Questions.Add(question);
        await _context.SaveChangesAsync();

        return Ok(_mapper.Map<QuestionDto>(question));
    }

    
[HttpPost("quizzes/{quizId}/submit")]
public async Task<IActionResult> SubmitQuiz(int quizId, [FromBody] Dictionary<int, string> answers, [FromQuery] int userId)
{
    if (userId <= 0)
        return BadRequest("Invalid userId");

    if (answers == null || !answers.Any())
        return BadRequest("Answers are required");

    
    var alreadyAttempted = await _context.Results
        .AnyAsync(r => r.UserId == userId && r.QuizId == quizId);

    if (alreadyAttempted)
        return BadRequest("You have already attempted this quiz");

    var questions = await _context.Questions
        .Where(q => q.QuizId == quizId)
        .ToListAsync();

    if (!questions.Any())
        return NotFound(new { message = "Quiz not found" });

    int score = 0;

    foreach (var q in questions)
    {
        if (answers.ContainsKey(q.QuestionId) &&
            answers[q.QuestionId] == q.CorrectAnswer)
        {
            score++;
        }
    }

    var result = new Result
    {
        QuizId = quizId,
        UserId = userId,
        Score = score,
        AttemptDate = DateTime.Now
    };

    _context.Results.Add(result);
    await _context.SaveChangesAsync();

    return Ok(new { Score = score });
}

    [HttpPut("questions/{id}")]
    public async Task<IActionResult> UpdateQuestion(int id, QuestionDto dto)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        var question = await _context.Questions.FindAsync(id);

        if (question == null)
            return NotFound(new { message = "Question not found" });

        _mapper.Map(dto, question);

        _context.Questions.Update(question);
        await _context.SaveChangesAsync();

        return Ok(_mapper.Map<QuestionDto>(question));
    }

    [HttpDelete("questions/{id}")]
    public async Task<IActionResult> DeleteQuestion(int id)
    {
        var question = await _context.Questions.FindAsync(id);

        if (question == null)
            return NotFound(new { message = "Question not found" });

        _context.Questions.Remove(question);
        await _context.SaveChangesAsync();

        return Ok(new
        {
            message = "Question deleted successfully",
            deletedQuestionId = id
        });
    }

    [HttpGet("quizzes/single/{id}")]
    public async Task<IActionResult> GetQuizById(int id)
    {
        var quiz = await _context.Quizzes.FindAsync(id);

        if (quiz == null)
            return NotFound();

        return Ok(quiz);
}
}