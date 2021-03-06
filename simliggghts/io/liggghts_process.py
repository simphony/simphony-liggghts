""" LIGGGHTS Process

This module provides a way to run the liggghts
"""

import os
import subprocess


class LiggghtsProcess(object):
    """ Class runs the liggghts program

    Parameters
    ----------
    liggghts_name : str
        name of LIGGGHTS executable
    log_directory : str, optional
        name of directory of log file ('log.liggghts') for liggghts.
        If not given, then pwd is where 'log.liggghts' will be written.

    Raises
    ------
    RuntimeError
        if liggghts did not run correctly
    """
    def __init__(self, liggghts_name="liggghts", log_directory=None):
        self._liggghts_name = liggghts_name
        self._returncode = 0
        self._stderr = ""
        self._stdout = ""
        if log_directory:
            self._log = os.path.join(log_directory, 'log.liggghts')
        else:
            self._log = 'log.liggghts'

        # see if liggghts can be started
        try:
            self.run(" ")
        except Exception:
            msg = "LIGGGHTS could not be started."
            if self._returncode == 127:
                msg += " executable '{}' was not found.".format(liggghts_name)
            else:
                msg += " stdout/err: " + self._stdout + " " + self._stderr
            raise RuntimeError(msg)

    def run(self, commands):
        """Run liggghts with a set of commands

        Parameters
        ----------
        commands : str
            set of commands to run

        Raises
        ------
        RuntimeError
            if Liggghts did not run correctly
        """

        proc = subprocess.Popen(
            [self._liggghts_name, '-log', self._log], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._stdout, self._stderr = proc.communicate(commands)
        self._returncode = proc.returncode

        if self._returncode != 0 or self._stderr:
            msg = "LIGGGHTS ('{}') did not run correctly. ".format(
                self._liggghts_name)
            msg += "Error code: {} ".format(proc.returncode)
            if self._stderr:
                msg += "stderr: \'{}\n\' ".format(self._stderr)
            if self._stdout:
                msg += "stdout: \'{}\n\'".format(self._stdout)
            raise RuntimeError(msg)
