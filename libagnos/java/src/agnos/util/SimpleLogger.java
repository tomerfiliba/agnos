package agnos.util;

import java.io.IOException;
import java.util.Date;
import java.util.logging.FileHandler;
import java.util.logging.Logger;
import java.util.logging.Level;
import java.util.logging.LogRecord;
import java.util.logging.Formatter;
import java.util.HashMap;
import java.lang.management.ManagementFactory;
import java.io.PrintWriter;
import java.io.StringWriter;


public class SimpleLogger
{
	static class OneLinerFormatter extends Formatter
	{
		@Override
		public String format(LogRecord record)
		{
			long millis = record.getMillis();
			Date d = new Date(millis);
			String str = String.format("%04d-%02d-%02d %02d:%02d:%02d.%03d|%-8s|%-8s|thd %4d|%s\n", 
					1900 + d.getYear(), d.getMonth(), d.getDay(), d.getHours(), d.getMinutes(), d.getSeconds(), millis % 1000, 
					record.getLoggerName(), record.getLevel().toString(), record.getThreadID(), record.getMessage());
			if (record.getThrown() != null) {
				StringWriter sw = new StringWriter(5000);
				PrintWriter pw = new PrintWriter(sw, true);
				record.getThrown().printStackTrace(pw);
				pw.flush();
				sw.flush();
				String[] lines = sw.toString().split("\r\n|\r|\n");
				for (String line : lines) {
					str += line + "\n";
				}
			}
			return str;
		}
	}
	
	private static FileHandler fh = null;
	static {
		String pid = ManagementFactory.getRuntimeMXBean().getName().split("@")[0];
		try {
			fh = new FileHandler("libagnos-java" + pid + ".log");
			fh.setFormatter(new OneLinerFormatter());
		}
		catch (IOException ex) {
			// ignore
		}
	}
	private static HashMap<String, Logger> loggerCache = new HashMap<String, Logger>();
	
	public static Logger getLogger(String name)
	{
		if (loggerCache.containsKey(name)) {
			return loggerCache.get(name);
		}
		Logger logger = Logger.getLogger(name);
		if (fh != null) {
			logger.addHandler(fh);
		}
		logger.setUseParentHandlers(false);
		logger.setLevel(Level.ALL);
		loggerCache.put(name, logger);
		return logger;
	}
	
}