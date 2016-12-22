#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import shlex
import time
import threading


class ProcessHandle(object):
    """进程句柄wrap
    """
    def __init__(self, handle, thread_timer=None):
        self.handle = handle
        self.thread_timer = thread_timer

    def kill(self):
        """杀死进程，忽略异常
        """
        ret = None
        try:
            if self.thread_timer:
                self.thread_timer.cancel()
        except Exception as e:
            pass
        try:
            ret = self.handle.kill()
        except Exception as e:
            pass
        return ret

    def poll(self):
        """poll"""
        return self.handle.poll()

    def send_sigint(self):
        """发送SIGINT，相对kill来对于某些进程来说更优雅，仅支持linux和mac"""
        ret = None
        try:
            if self.thread_timer:
                self.thread_timer.cancel()
        except Exception as e:
            pass
        try:
            import signal
            ret = self.handle.send_signal(signal.SIGINT)
            time.sleep(1) # 续命1秒
        except Exception as e:
            pass
        return ret

    def wait(self):
        """wait"""
        return self.handle.wait()


class Cmd(object):
    """带TimeOut的执行命令

    这个保证windows和linux两个平台下都能有效的保证subprocess.Popen起来的进程能正确的阻塞执行，
    并在超过timeout后被杀死；同时通过保持读输出通道避免了默认subprocess.PIPE在写满后阻塞被执行进程运行
    """
    @classmethod
    def run(cls, cmd, timeout=60, shell=False,
            watcher=None, output_file=None, output_callback=None, cwd=None):
        """执行命令
        Args:
            cmd: string, 待执行命令
            timeout: int, 等待超时时间，单位秒
        """
        return Cmd.__run(cmd, timeout, shell, watcher, output_file, output_callback, cwd=cwd)

    @classmethod
    def async(cls, cmd, timeout=-1, shell=False,
            watcher=None, output_file=None, output_callback=None, cwd=None):
        """异步执行命令，参数同run方法
        """
        return Cmd.__run(cmd, timeout, shell, watcher, output_file=output_file,
                output_callback=output_callback, wait=False, cwd=cwd)

    @classmethod
    def __run(cls, cmd, timeout, shell,
            watcher, output_file=None, output_callback=None, wait=True, cwd=None):
        phandle, ret_code = None, -1
        try:
            if shell is False:
                cmd = shlex.split(cmd)
            def _stream_watcher(stream, output, name=''):
                while True:
                    line = stream.readline()
                    if line:
                        if output_callback:
                            output_callback(line)
                        output.append(line)
                    else:
                        break
                if not stream.closed:
                    stream.close()
            phandle = subprocess.Popen(cmd, shell=shell,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd)
            start_time = time.time()
            stdout = []
            thread_watch_stdout = threading.Thread(target=_stream_watcher,
                    kwargs={'stream': phandle.stdout, 'output': stdout, 'name': 'stdout'})
            thread_watch_stdout.setDaemon(True)
            thread_watch_stdout.start()
            if watcher:
                thread_watcher = threading.Thread(target=watcher, kwargs={'handle': phandle})
                thread_watcher.setDaemon(True)
                thread_watcher.start()
            timeout_flag = threading.Event()
            thread_timer = None
            if timeout > 0:
                def _timeout(flag):
                    if phandle.poll() is None:
                        if flag.is_set() is False:
                            flag.set()
                            if phandle:
                                phandle.kill()
                thread_timer = threading.Timer(timeout, _timeout, kwargs={'flag': timeout_flag})
                thread_timer.setDaemon(True)
                thread_timer.start()
            phandle = ProcessHandle(phandle, thread_timer)
            if wait is False:
                # 非阻塞运行，返回进程handle
                return phandle, stdout
            ret_code = phandle.wait()
            if thread_timer:
                thread_timer.cancel()
            thread_watch_stdout.join(1)
            if watcher:
                thread_watcher.join(1)
            if output_file:
                fd = open(output_file, 'w')
                for line in stdout:
                    fd.write(line)
                fd.close()
            if timeout_flag.is_set():
                return -1, stdout
            else:
                return ret_code, stdout
        except Exception as e:
            if phandle:
                phandle.kill()
            raise e
        return -1, []