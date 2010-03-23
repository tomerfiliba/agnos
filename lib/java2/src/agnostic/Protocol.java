import java.io.*;
import java.util.*;

public class Protocol
{
	protected InputStream	inStream;
	protected OutputStream	outStream;

	public Protocol(InputStream inStream, OutputStream outStream)
	{
		this.inStream = instream;
		this.outStream = outstream;
	}

	protected void _write(byte[] buffer) throws IOException
	{
		outStream.write(buffer, 0, buffer.length);
	}

	protected void _read(byte[] buffer) throws IOException
	{
		int total_got = 0;
		int got;

		while (total_got < buffer.length) {
			got = inStream.read(buffer, total_got, buffer.length - total_got);
			count += got;
			if (got <= 0 && total_got < buffer.length) {
				throw new IOException("end of stream detected");
			}
		}
	}

	private byte[]	_int8_buf	= new byte[1];

	public void write_int8(byte val) throws IOException
	{
		_int8_buf[0] = val;
		_write(_int8_buf);
	}

	public byte read_int8() throws IOException
	{
		_read(_int8_buf);
		return _int8_buf[0];
	}

	private byte[]	_int16_buf	= new byte[2];

	public void write_int16(short val) throws IOException
	{
		_int16_buf[1] = (byte) ((val >> 8) & 0xff);
		_int16_buf[0] = (byte) (val & 0xff);
		_write(_int16_buf);
	}

	public short read_int16() throws IOException
	{
		_read(_int16_buf);
		return (short) (_int16_buf[1] << 8 | _int16_buf[0]);
	}

	private byte[]	_int32_buf	= new byte[4];

	public void write_int32(int val) throws IOException
	{
		_int32_buf[3] = (byte) ((val >> 24) & 0xff);
		_int32_buf[2] = (byte) ((val >> 16) & 0xff);
		_int32_buf[1] = (byte) ((val >> 8) & 0xff);
		_int32_buf[0] = (byte) (val & 0xff);
		_write(_int32_buf);
	}

	public int read_int32() throws IOException
	{
		_read(_int32_buf);
		return (int) (_int32_buf[3] << 24 | _int32_buf[2] << 16
				| _int32_buf[1] << 8 | _int32_buf[0]);
	}

	private byte[]	_int64_buf	= new byte[8];

	public void write_int64(long val) throws IOException
	{
		_int32_buf[7] = (byte) ((val >> 56) & 0xff);
		_int32_buf[6] = (byte) ((val >> 48) & 0xff);
		_int32_buf[5] = (byte) ((val >> 40) & 0xff);
		_int32_buf[4] = (byte) ((val >> 32) & 0xff);
		_int32_buf[3] = (byte) ((val >> 24) & 0xff);
		_int32_buf[2] = (byte) ((val >> 16) & 0xff);
		_int32_buf[1] = (byte) ((val >> 8) & 0xff);
		_int32_buf[0] = (byte) (val & 0xff);
		_write(_int64_buf);
	}

	public long read_int64() throws IOException
	{
		_read(_int64_buf);
		return (long) (_int32_buf[7] << 56 | _int32_buf[6] << 48
				| _int32_buf[5] << 40 | _int32_buf[4] << 32
				| _int32_buf[3] << 24 | _int32_buf[2] << 16
				| _int32_buf[1] << 8 | _int32_buf[0]);
	}

	public void write_float(double val) throws IOException
	{
		write_int64(Double.doubleToLongBits(val));
	}

	public double read_float() throws IOException
	{
		return Double.longBitsToDouble(read_int64());
	}

	public void write_bool(boolean val) throws IOException
	{
		write_int8(val ? (byte) 1 : (byte) 0);
	}

	public boolean read_bool() throws IOException
	{
		return read_int8() != 0;
	}

	public void write_date(Date date) throws IOException
	{
		write_int64(date.getTime());
	}

	public Date read_date() throws IOException
	{
		return new Date(read_int64());
	}

	public void write_string(String val) throws IOException
	{
		write_int32(val.length());
		_write(val.getBytes("UTF-8"))
	}

	public String read_string() throws IOException
	{
		int len = read_int32();
		byte[] buffer = new buffer[len];
		_read(buffer);
		return new String(buffer, "UTF-8");
	}

	public void write_buffer(byte[] val) throws IOException
	{
		write_int32(val.length);
		_write(val)
	}

	public byte[] read_buffer() throws IOException
	{
		int len = read_int32();
		byte[] buffer = new buffer[len];
		_read(buffer);
		return buffer;
	}
	
	public void write_list(List val) throws IOException
	{
		write_int32(val.size());
		Iterator it = val.iterator();
		while (it.hasNext()) {
			type.pack(it.next(), stream);
		}
		
	}

	public List read_list(type) throws IOException
	{
		int len = read_int32();
		ArrayList<Object> arr = new ArrayList<Object>(len);
		for (int i = 0; i < len; i++) {
			arr.add(type.unpack(stream));
		}
		return arr;
	}

}


























