# -*- coding: utf-8 -*-
"""
This library uses jhove to detect corrupt PDFs and qpdf to fix them
"""
import os
import re
import sys
import magic

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess


class PDFError(Exception):
    def __init__(self, output):
        self.output = output

class PDFNotFound(PDFError):
    pass

class PDFInvalidMimeType(PDFError):
    pass


class PDFFixer(object):
    """
    Class to detect corrupted PDF and fix them
    """
    def __init__(self, pdf_path):
        # Security checks
        if not os.path.exists(pdf_path) or not os.path.isfile(pdf_path) or not \
        os.access(pdf_path, os.R_OK):
            raise PDFNotFound(u"{} not found or not readable".format(
                pdf_path.decode('utf8')))

        if not re.search("PDF document", magic.from_file(pdf_path)):
            raise PDFInvalidMimeType(u"{} is not a PDF file".format(
                pdf_path.decode('utf8')))

        self.pdf_path = pdf_path.decode('utf8')

        # TODO: Check OS
        self._jhove_exec = "jhove"
        self._qpdf_exec = "qpdf"

    def has_errors(self, timeout=None):
        """Check if PDF file has errors using jhove"""
        args = [self._jhove_exec, '-m', 'pdf-hul', self.pdf_path]

        process_output = None
        try:
            process_output = subprocess.check_output(args,
                                                     stderr=subprocess.STDOUT,
                                                     timeout=timeout)
        except subprocess.TimeoutExpired as e:
            raise PDFError(u"Could not check errors in {}".format(
                self.pdf_path))
        except subprocess.CalledProcessError as e:
            raise PDFError(process_output if process_output else e.message)
        else:
            return re.search('Not well-formed', process_output) is not None

    def fix_errors(self, timeout=None):
        """Try to fix errors in PDF using qpdf"""
        pdf_filename = os.path.splitext(os.path.basename(self.pdf_path))[0]
        pdf_dirpath = os.path.dirname(self.pdf_path)
        fixed_pdf_path = u"{}/{}_fixed.pdf".format(pdf_dirpath, pdf_filename)
        args = [self._qpdf_exec, self.pdf_path, fixed_pdf_path]

        process_output = None
        try:
            process_output = subprocess.check_output(args,
                                                     stderr=subprocess.STDOUT,
                                                     timeout=timeout)
        except subprocess.TimeoutExpired as e:
            raise PDFError(u"Could not check errors in {}".format(
                self.pdf_path))
        except subprocess.CalledProcessError as e:
            # This is not necessarily an error
            if re.search("operation succeeded", e.output):
                return fixed_pdf_path
            else:
                raise PDFError(process_output if process_output else e.message)
        else:
            return fixed_pdf_path
