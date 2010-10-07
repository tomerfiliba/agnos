//////////////////////////////////////////////////////////////////////////////
//
// Code inspired by the not-yet-official Boost::Process
// http://www.highscore.de/boost/process/
//
//////////////////////////////////////////////////////////////////////////////
#include <boost/config.hpp>
#include <boost/system/config.hpp>
#include <boost/iostreams/stream.hpp>
#include <boost/process/detail/file_handle.hpp>
#include <boost/process/detail/systembuf.hpp>
#include <istream>
#include <ostream>
#include "process.hpp"


#define BOOST_POSIX_API

#if defined(BOOST_POSIX_API)
#	include <unistd.h>
#	include <stdlib.h>
#	include <fcntl.h>
#	include <sys/types.h>
#	include <signal.h>
#	include <sys/wait.h>
#elif defined(BOOST_WINDOWS_API)
#	include <windows.h>
#endif



namespace agnos
{
	namespace utils
	{
		class opstream : public std::ostream, public boost::noncopyable
		{
		protected:
			boost::detail::file_handle handle_;
			boost::detail::systembuf systembuf_;

		public:
			explicit opstream(detail::file_handle &fh) :
				std::ostream(0),
				handle_(fh),
				systembuf_(handle_.get())
			{
				rdbuf(&systembuf_);
			}

			detail::file_handle &handle()
			{
				return handle_;
			}

			void close()
			{
				systembuf_.sync();
				handle_.close();
			}
		};

		class ipstream : public std::istream, public boost::noncopyable
		{
		private:
			boost::detail::file_handle handle_;
			boost::detail::systembuf systembuf_;

		public:
			explicit ipstream(detail::file_handle &fh) :
				std::istream(0),
				handle_(fh),
				systembuf_(handle_.get())
			{
				rdbuf(&systembuf_);
			}

			detail::file_handle &handle()
			{
				return handle_;
			}

			void close()
			{
				handle_.close();
			}
		};


#if defined(BOOST_POSIX_API)
		class PosixProcess : public Process
		{
		protected:
			pid_t _pid;
			mutable int _retcode;
			mutable bool _running;
			shared_ptr<opstream> _stdin;
			shared_ptr<ipstream> _stdout;
			shared_ptr<ipstream> _stderr;

			PosixProcess(const ProcessFactory& factory) : _pid(-1), _retcode(-1), _running(false)
			{
				int fds[3][2];

				for (int i = 0; i < 3; i++) {
					if (pipe(fds[i]) != 0) {
						boost::throw_exception(boost::system::system_error(
								boost::system::error_code(errno, boost::system::get_system_category()),
								"PosixProcess: pipe() failed"));
					}
				}

				pid_t pid = ::fork();
				if (pid == -1) {
					boost::throw_exception(boost::system::system_error(
							boost::system::error_code(errno, boost::system::get_system_category()),
							"PosixProcess: fork() failed"));
				}
				// child
				else if (pid == 0) {
					::close(fds[0][1]);
					::close(fds[1][0]);
					::close(fds[2][0]);
					dup2(fds[0][0], 0);
					dup2(fds[1][1], 1);
					dup2(fds[2][1], 2);

					if (!inherit_handles) {
						int maxdescs = -1;
#if defined(F_MAXFD)
						maxdescs = ::fcntl(-1, F_MAXFD, 0);
#endif
						if (maxdescs < 0) {
							maxdescs = ::sysconf(_SC_OPEN_MAX);
						}
						if (maxdescs < 0) {
							maxdescs = 1024;
						}
						for (int i = 0; i < maxdescs; i++) {
							// ignore errors
							::close(i);
						}
					}

					if (!factory.env.workdir.empty()) {
						chdir(factory.env.workdir.c_str());
					}

					char * args[factory.args.size() + 1];
					for (int i = 0; i < factory.args.size(); i++) {
						args[i] = factory.args[i].c_str();
					}
					args[factory.args.size()] = NULL;

					if (inherit_env) {
						map<string,string>::const_iterator it;
						for (it = factory.env.begin(); it != factory.env.end(); it++) {
							if (setenv(it->first, it->second, 1) != 0) {
								boost::throw_exception(boost::system::system_error(
										boost::system::error_code(errno, boost::system::get_system_category()),
										"PosixProcess: setenv() failed"));
							}
						}
						::execv(facotry.executable.c_str(), args);
					}
					else {
						char * env[factory.env.size() + 1];
						string formatted[factory.env.size()];

						int i = 0;
						map<string,string>::const_iterator it;
						for (i = 0, it = factory.env.begin(); it != factory.env.end(); it++, i++) {
							formatted[i] = it->first + "=" + it->second;
							env[i] = formatted[i].c_str();
						}
						env[factory.args.size()] = NULL;
						::execve(facotry.executable.c_str(), args, env);
					}

					// if we got here, exec() failed
					boost::throw_exception(boost::system::system_error(
							boost::system::error_code(errno, boost::system::get_system_category()),
							"PosixProcess: exec() failed"));
					// and just in case
					std::exit(1);
				}
				// parent
				else {
					::close(fds[0][0]);
					::close(fds[1][1]);
					::close(fds[2][1]);

					_pid = pid;
					_running = true;

					_stdin.reset(new opstream(fds[0][1]));
					_stdout.reset(new opstream(fds[1][0]));
					_stderr.reset(new opstream(fds[2][0]));
				}
			}

		public:
			int pid() const
			{
				return (int)_pid;
			}

			int retcode() const
			{
				if (_running) {
					return -1;
				}
				else {
					return _retcode;
				}
			}

			bool _wait(int options) const
			{
				int status;
				pid_t ret = ::waitpid(_pid, &status, WNOHANG);

				if (ret < 0) {
					boost::throw_exception(boost::system::system_error(
							boost::system::error_code(errno, boost::system::get_system_category()),
							"PosixProcess: waitpid() failed"));
				}
				else if (ret == 0) {
					return false;
				}
				else {
					_retcode = WEXITSTATUS(ret);
					_running = false;
					return true;
				}
			}

			void wait() const
			{
				_wait(_pid, 0);
			}

			bool alive() const
			{
				return !_wait(_pid, WNOHANG);
			}

			void signal(int signum)
			{
				if (!_running) {
					throw ChildProcessError("signal: process not running");
				}
				if (kill(_pid, signum) != 0) {
					boost::throw_exception(boost::system::system_error(
							boost::system::error_code(errno, boost::system::get_system_category()),
							"PosixProcess: kill() failed"));
				}
			}

			void terminate(bool force)
			{
				signal(force ? SIGKILL : SIGTERM);
			}

			ostream& stdin() const
			{
				return *_stdin;
			}

			istream& stdout() const
			{
				return *_stdout;
			}

			istream& stderr() const
			{
				return *_stderr;
			}

		};

		typedef PosixProcess ProcessImpl;

#elif defined(BOOST_WINDOWS_API)
		class Win32Process : public Process
		{
		protected:
			Win32Process(const ProcessFactory& factory)
			{
				throw ChildProcessError("unsupported platform");
			}
		};

		typedef Win32Process ProcessImpl;

#else
		class DummyProcess : public Process
		{
		protected:
			DummyProcess(const ProcessFactory& factory)
			{
				throw ChildProcessError("unsupported platform");
			}
		};

		typedef DummyProcess ProcessImpl;
#endif

		//////////////////////////////////////////////////////////////////////

		ProcessFactory::ProcessFactory(const string& executable) :
				executable(executable),
				inherit_env(true),
				inherit_handles(false)
		{
		}

		ProcessFactory::ProcessFactory(const string& executable, const vector<string> args) :
				executable(executable),
				args(args),
				inherit_env(true),
				inherit_handles(false)
		{
		}

		shared_ptr<Process> ProcessFactory::start()
		{
			shared_ptr<Process> proc(ProcessImpl(*this));
			return proc;
		}

	}
}



