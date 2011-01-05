package agnos.util;

import java.io.IOException;

public class UnknownPackerId extends IOException
{
	private static final long serialVersionUID = -6986473780293444226L;

	public UnknownPackerId(String message)
	{
		super(message);
	}
}
