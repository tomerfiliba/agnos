
namespace agnos
{
	class InputStream
	{
		public virtual ssize_t read(void * buf, size_t count) = 0;
		public virtual void close() = 0;
	};

	class OutputStream
	{
		public virtual ssize_t write(void * buf, size_t count) = 0;
		public virtual void close() = 0;
	};

	class BufferedInputStream : InputStream
	{
		InputStream& stream;
		size_t buffer_size;
		size_t in_buffer;
		uint8_t * buffer;

		public BufferedInputStream(InputStream& stream, size_t buffer_size)
		{
			this->stream = stream;
			this->buffer_size = buffer_size;
			buffer = new uint8_t[buffer_size];
			in_buffer = 0;
		}

		~BufferedInputStream()
		{
			delete buffer;
		}

		public void close()
		{
			stream.close();
		}

	    private ssize_t _read(void * buf, size_t count)
	    {
	        while (count > 0) {
				stream.read()

	        }
	    }
	        bufs = []
	            data = self.file.read(max(count, self.bufsize))
	            if not data:
	                raise EOFError("premature end of stream detected")
	            bufs.append(data)
	            count -= len(data)
	        return "".join(bufs)

		public ssize_t read(void * buf, size_t count)
		{
			if (count <= in_buffer) {
				in_buffer -= count;
				memcpy(buf, buffer, count);
				return count;
			}
			else {
				size_t req = count - in_buffer;
				stream.read
				memcpy(buf, buffer, count);
			}

            req = count - len(self.buffer)
            data2 = self._read(req)
            data = self.buffer + data2[:req]
            self.buffer = data2[req:]
		}
	};


	class IPacker
	{
		public virtual pack(void * obj, ostream stream) = 0;
		public virtual unpack(istream stream) = 0;

		public static write(ostream stream, char * buf, size_t size)
		{
			stream.
		}
	};

	class Int8Packer
	{
		public pack(void * obj, ostream stream)
		{
			int8_t val = 0;
			if (obj != NULL) {
				val = *((int8_t*)obj)
			}

		}

		public virtual unpack(ostream stream) = 0;
	};


}
