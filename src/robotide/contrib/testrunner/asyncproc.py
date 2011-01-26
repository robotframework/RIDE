#! /usr/bin/env python

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  The text of the license conditions can be read at
#  <http://www.lysator.liu.se/~bellman/download/gpl-3.0.txt>
#  or at <http://www.gnu.org/licenses/>.

# original source:
# http://www.lysator.liu.se/~bellman/download/asyncproc.py
#
# modified by Bryan Oakley (bryan.oakley@orbitz.com) to run on Windows
# by adding a poll() method (because Windows doesn't support
# wait(os.WNOHANG)), and using SIGTERM rather than SIGKILL (since
# Windows doesn't support signal.SIGKILL)

__rcsId__ = """$Id: asyncproc.py,v 1.9 2007/08/06 18:29:24 bellman Exp $"""
__author__ = "Thomas Bellman <bellman@lysator.liu.se>"
__url__ = "http://www.lysator.liu.se/~bellman/download/"
__licence__ = "GNU General Publice License version 3 or later"


import os
import time
import errno
import signal
import threading
import subprocess

# on unixy systems SIGKILL is the Right Thing To Do. On some
# platforms (*windows* *cough*) that signal isn't supported
SIGKILL = getattr(signal, "SIGKILL", signal.SIGTERM)

__all__ = [ 'Process', 'with_timeout', 'Timeout' ]


class Timeout(Exception):
    """Exception raised by with_timeout() when the operation takes too long.
    """
    pass


def with_timeout(timeout, func, *args, **kwargs):
    """Call a function, allowing it only to take a certain amount of time.
       Parameters:
	- timeout	The time, in seconds, the function is allowed to spend.
			This must be an integer, due to limitations in the
			SIGALRM handling.
	- func		The function to call.
	- *args		Non-keyword arguments to pass to func.
	- **kwargs	Keyword arguments to pass to func.

       Upon successful completion, with_timeout() returns the return value
       from func.  If a timeout occurs, the Timeout exception will be raised.

       If an alarm is pending when with_timeout() is called, with_timeout()
       tries to restore that alarm as well as possible, and call the SIGALRM
       signal handler if it would have expired during the execution of func.
       This may cause that signal handler to be executed later than it would
       normally do.  In particular, calling with_timeout() from within a
       with_timeout() call with a shorter timeout, won't interrupt the inner
       call.  I.e.,
	    with_timeout(5, with_timeout, 60, time.sleep, 120)
       won't interrupt the time.sleep() call until after 60 seconds.
    """

    class SigAlarm(Exception):
	"""Internal exception used only within with_timeout().
	"""
	pass

    def alarm_handler(signum, frame):
	raise SigAlarm()

    oldalarm = signal.alarm(0)
    oldhandler = signal.signal(signal.SIGALRM, alarm_handler)
    try:
	try:
	    t0 = time.time()
	    signal.alarm(timeout)
	    retval = func(*args, **kwargs)
	except SigAlarm:
	    raise Timeout("Function call took too long", func, timeout)
    finally:
	signal.alarm(0)
	signal.signal(signal.SIGALRM, oldhandler)
	if oldalarm != 0:
	    t1 = time.time()
	    remaining = oldalarm - int(t1 - t0 + 0.5)
	    if remaining <= 0:
		# The old alarm has expired.
		os.kill(os.getpid(), signal.SIGALRM)
	    else:
		signal.alarm(remaining)

    return retval



class Process(object):
    """Manager for an asynchronous process.
       The process will be run in the background, and its standard output
       and standard error will be collected asynchronously.

       Since the collection of output happens asynchronously (handled by
       threads), the process won't block even if it outputs large amounts
       of data and you do not call Process.read*().

       Similarly, it is possible to send data to the standard input of the
       process using the write() method, and the caller of write() won't
       block even if the process does not drain its input.

       On the other hand, this can consume large amounts of memory,
       potentially even exhausting all memory available.

       Parameters are identical to subprocess.Popen(), except that stdin,
       stdout and stderr default to subprocess.PIPE instead of to None.
       Note that if you set stdout or stderr to anything but PIPE, the
       Process object won't collect that output, and the read*() methods
       will always return empty strings.  Also, setting stdin to something
       other than PIPE will make the write() method raise an exception.
    """

    def __init__(self, *params, **kwparams):
	if len(params) <= 3:
	    kwparams.setdefault('stdin', subprocess.PIPE)
	if len(params) <= 4:
	    kwparams.setdefault('stdout', subprocess.PIPE)
	if len(params) <= 5:
	    kwparams.setdefault('stderr', subprocess.PIPE)
	self.__pending_input = []
	self.__collected_outdata = []
	self.__collected_errdata = []
	self.__exitstatus = None
	self.__lock = threading.Lock()
	self.__inputsem = threading.Semaphore(0)
	# Flag telling feeder threads to quit
	self.__quit = False

	self.__process = subprocess.Popen(*params, **kwparams)

	if self.__process.stdin:
	    self.__stdin_thread = threading.Thread(
		name="stdin-thread",
		target=self.__feeder, args=(self.__pending_input,
					    self.__process.stdin))
	    self.__stdin_thread.setDaemon(True)
	    self.__stdin_thread.start()
	if self.__process.stdout:
	    self.__stdout_thread = threading.Thread(
		name="stdout-thread",
		target=self.__reader, args=(self.__collected_outdata,
					    self.__process.stdout))
	    self.__stdout_thread.setDaemon(True)
	    self.__stdout_thread.start()
	if self.__process.stderr:
	    self.__stderr_thread = threading.Thread(
		name="stderr-thread",
		target=self.__reader, args=(self.__collected_errdata,
					    self.__process.stderr))
	    self.__stderr_thread.setDaemon(True)
	    self.__stderr_thread.start()

    def __del__(self, __killer=os.kill, __sigkill=SIGKILL):
	if self.__exitstatus is None:
	    __killer(self.pid(), __sigkill)

    def poll(self):
        """Checks to see if the process has terminated. 
        If so, the return code is returned. Otherwise None is returned"""
        return self.__process.poll()

    def pid(self):
	"""Return the process id of the process.
	   Note that if the process has died (and successfully been waited
	   for), that process id may have been re-used by the operating
	   system.
	"""
	return self.__process.pid

    def kill(self, signal):
	"""Send a signal to the process.
	   Raises OSError, with errno set to ECHILD, if the process is no
	   longer running.
	"""
	if self.__exitstatus is not None:
	    # Throwing ECHILD is perhaps not the most kosher thing to do...
	    # ESRCH might be considered more proper.
	    raise OSError(errno.ECHILD, os.strerror(errno.ECHILD))
	if os.name == 'nt':
		import ctypes
		kernel32 = ctypes.windll.kernel32
		handle = kernel32.OpenProcess(1, 0, self.pid())
		kernel32.TerminateProcess(handle, 0)
	else:
		os.kill(self.pid(), signal)

    def wait(self, flags=0):
	"""Return the process' termination status.

	   If bitmask parameter 'flags' contains os.WNOHANG, wait() will
	   return None if the process hasn't terminated.  Otherwise it
	   will wait until the process dies.

	   It is permitted to call wait() several times, even after it
	   has succeeded; the Process instance will remember the exit
	   status from the first successful call, and return that on
	   subsequent calls.
	"""
	if self.__exitstatus is not None:
	    return self.__exitstatus
	pid,exitstatus = os.waitpid(self.pid(), flags)
	if pid == 0:
	    return None
	if os.WIFEXITED(exitstatus) or os.WIFSIGNALED(exitstatus):
	    self.__exitstatus = exitstatus
	    # If the process has stopped, we have to make sure to stop
	    # our threads.  The reader threads will stop automatically
	    # (assuming the process hasn't forked), but the feeder thread
	    # must be signalled to stop.
	    if self.__process.stdin:
		self.closeinput()
	    # We must wait for the reader threads to finish, so that we
	    # can guarantee that all the output from the subprocess is
	    # available to the .read*() methods.
	    # And by the way, it is the responsibility of the reader threads
	    # to close the pipes from the subprocess, not our.
	    if self.__process.stdout:
		self.__stdout_thread.join()
	    if self.__process.stderr:
		self.__stderr_thread.join()
	return exitstatus

    def terminate(self, graceperiod=1):
	"""Terminate the process, with escalating force as needed.
	   First try gently, but increase the force if it doesn't respond
	   to persuassion.  The levels tried are, in order:
	    - close the standard input of the process, so it gets an EOF.
	    - send SIGTERM to the process.
	    - send SIGKILL to the process.
	   terminate() waits up to GRACEPERIOD seconds (default 1) before
	   escalating the level of force.  As there are three levels, a total
	   of (3-1)*GRACEPERIOD is allowed before the process is SIGKILL:ed.
	   GRACEPERIOD must be an integer, and must be at least 1.
	      If the process was started with stdin not set to PIPE, the
	   first level (closing stdin) is skipped.
	"""
	if self.__process.stdin:
	    # This is rather meaningless when stdin != PIPE.
	    self.closeinput()
	    try:
		return with_timeout(graceperiod, self.wait)
	    except Timeout:
		pass

	self.kill(signal.SIGTERM)
	try:
	    return with_timeout(graceperiod, self.wait)
	except Timeout:
	    pass

	self.kill(SIGKILL)
	return self.wait()

    def __reader(self, collector, source):
	"""Read data from source until EOF, adding it to collector.
	"""
	while True:
	    data = os.read(source.fileno(), 65536)
	    self.__lock.acquire()
	    collector.append(data)
	    self.__lock.release()
	    if data == "":
		source.close()
		break
	return

    def __feeder(self, pending, drain):
	"""Feed data from the list pending to the file drain.
	"""
	while True:
	    self.__inputsem.acquire()
	    self.__lock.acquire()
	    if not pending  and	 self.__quit:
		drain.close()
		self.__lock.release()
		break
	    data = pending.pop(0)
	    self.__lock.release()
	    drain.write(data)

    def read(self):
	"""Read data written by the process to its standard output.
	"""
	self.__lock.acquire()
	outdata = "".join(self.__collected_outdata)
	del self.__collected_outdata[:]
	self.__lock.release()
	return outdata

    def readerr(self):
	"""Read data written by the process to its standard error.
	"""
	self.__lock.acquire()
	errdata = "".join(self.__collected_errdata)
	del self.__collected_errdata[:]
	self.__lock.release()
	return errdata

    def readboth(self):
	"""Read data written by the process to its standard output and error.
	   Return value is a two-tuple ( stdout-data, stderr-data ).

	   WARNING!  The name of this method is ugly, and may change in
	   future versions!
	"""
	self.__lock.acquire()
	outdata = "".join(self.__collected_outdata)
	del self.__collected_outdata[:]
	errdata = "".join(self.__collected_errdata)
	del self.__collected_errdata[:]
	self.__lock.release()
	return outdata,errdata

    def _peek(self):
	self.__lock.acquire()
	output = "".join(self.__collected_outdata)
	error = "".join(self.__collected_errdata)
	self.__lock.release()
	return output,error

    def write(self, data):
	"""Send data to a process's standard input.
	"""
	if self.__process.stdin is None:
	    raise ValueError("Writing to process with stdin not a pipe")
	self.__lock.acquire()
	self.__pending_input.append(data)
	self.__inputsem.release()
	self.__lock.release()

    def closeinput(self):
	"""Close the standard input of a process, so it receives EOF.
	"""
	self.__lock.acquire()
	self.__quit = True
	self.__inputsem.release()
	self.__lock.release()


class ProcessManager(object):
    """Manager for asynchronous processes.
       This class is intended for use in a server that wants to expose the
       asyncproc.Process API to clients.  Within a single process, it is
       usually better to just keep track of the Process objects directly
       instead of hiding them behind this.  It probably shouldn't have been
       made part of the asyncproc module in the first place.
    """

    def __init__(self):
	self.__last_id = 0
	self.__procs = {}

    def start(self, args, executable=None, shell=False, cwd=None, env=None):
	"""Start a program in the background, collecting its output.
	   Returns an integer identifying the process.	(Note that this
	   integer is *not* the OS process id of the actuall running
	   process.)
	"""
	proc = Process(args=args, executable=executable, shell=shell,
		       cwd=cwd, env=env)
	self.__last_id += 1
	self.__procs[self.__last_id] = proc
	return self.__last_id

    def kill(self, procid, signal):
	return self.__procs[procid].kill(signal)

    def terminate(self, procid, graceperiod=1):
	return self.__procs[procid].terminate(graceperiod)

    def write(self, procid, data):
	return self.__procs[procid].write(data)

    def closeinput(self, procid):
	return self.__procs[procid].closeinput()

    def read(self, procid):
	return self.__procs[procid].read()

    def readerr(self, procid):
	return self.__procs[procid].readerr()

    def readboth(self, procid):
	return self.__procs[procid].readboth()

    def wait(self, procid, flags=0):
	"""
	   Unlike the os.wait() function, the process will be available
	   even after ProcessManager.wait() has returned successfully,
	   in order for the process' output to be retrieved.  Use the
	   reap() method for removing dead processes.
	"""
	return self.__procs[procid].wait(flags)

    def reap(self, procid):
	"""Remove a process.
	   If the process is still running, it is killed with no pardon.
	   The process will become unaccessible, and its identifier may
	   be reused immediately.
	"""
	if self.wait(procid, os.WNOHANG) is None:
	    self.kill(procid, SIGKILL)
	self.wait(procid)
	del self.__procs[procid]

    def reapall(self):
	"""Remove all processes.
	   Running processes are killed without pardon.
	"""
	# Since reap() modifies __procs, we have to iterate over a copy
	# of the keys in it.  Thus, do not remove the .keys() call.
	for procid in self.__procs.keys():
	    self.reap(procid)


def _P1():
    return Process(["tcpconnect", "-irv", "localhost", "6923"])

def _P2():
    return Process(["tcplisten", "-irv", "6923"])

