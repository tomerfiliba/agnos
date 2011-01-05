package agnos.packers;

public interface ISerializer
{
	Long store(Object obj);

	Object load(Long id);
}