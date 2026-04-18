using AutoMapper;
using MultiPageELearningApi.Models;
using MultiPageELearningApi.Dtos;
public class MappingProfile : Profile
{
    public MappingProfile()
    {
        CreateMap<User, UserDto>().ReverseMap();
        CreateMap<Course, CourseDto>().ReverseMap();
        CreateMap<CreateCourseDto, Course>();
        CreateMap<Lesson, LessonDto>().ReverseMap();
        CreateMap<Quiz, QuizDto>().ReverseMap();
        CreateMap<Question, QuestionDto>().ReverseMap();
        CreateMap<Result, ResultDto>().ReverseMap();
    }
}