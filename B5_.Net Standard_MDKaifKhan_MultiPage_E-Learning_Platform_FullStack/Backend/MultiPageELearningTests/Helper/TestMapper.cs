using AutoMapper;

public static class TestMapper
{
    public static IMapper GetMapper()
    {
        var config = new MapperConfiguration(cfg => { });
        return config.CreateMapper();
    }
}