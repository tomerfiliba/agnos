#ifndef AGNOS_PROCESS_HPP_INCLUDED
#define AGNOS_PROCESS_HPP_INCLUDED

#include "objtypes.hpp"
#include "utils.hpp"


namespace agnos
{
	namespace utils
	{
		DEFINE_EXCEPTION(ChildProcessError);

		class ProcessFactory;

		class Process : public boost::noncopyable
		{
		protected:
			friend class ProcessFactory;

			Process();

		public:
			virtual int pid() const = 0;
			virtual int retcode() const = 0;
			virtual void wait() const = 0;
			virtual bool alive() const = 0;

			virtual ostream& stdin() const = 0;
			virtual istream& stdout() const = 0;
			virtual istream& stderr() const = 0;

			virtual void signal(int signum) = 0;
			virtual void terminate(bool force = false) = 0;
		};

		class ProcessFactory
		{
		public:
			string executable;
			string workdir;
			vector<string> args;
			bool inherit_env;
			map<string, string> env;
			bool inherit_handles;

			ProcessFactory(const string& executable);
			ProcessFactory(const string& executable, const vector<string> args);

			Process start();
		};

	}
}


#endif // AGNOS_PROCESS_HPP_INCLUDED
