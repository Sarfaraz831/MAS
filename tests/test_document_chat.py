import unittest
from io import BytesIO
from unittest.mock import patch

from pypdf import PdfWriter
import requests

from document_chat import (
    analyze_copyright,
    analyze_safety,
    extract_pdf,
    extract_url,
    _validate_public_url,
)


class DocumentChatTests(unittest.TestCase):
    def test_copyright_check_reports_notice_and_does_not_claim_clearance(self):
        result = analyze_copyright("Copyright 2025 Example. All rights reserved.")

        self.assertEqual(result["status"], "indicators_found")
        self.assertIn("does not determine ownership", result["notice"])

    def test_copyright_check_does_not_infer_a_license_from_no_notice(self):
        result = analyze_copyright("A document with ordinary text.")

        self.assertEqual(result["status"], "no_indicators_found")
        self.assertEqual(result["indicators"], [])

    def test_safety_check_returns_advisory_flags_without_blocking(self):
        warnings = analyze_safety("This text says ignore previous instructions and mentions self-harm.")

        self.assertIn("possible embedded prompt instructions", warnings)
        self.assertIn("self-harm related content", warnings)

    def test_url_check_rejects_localhost_and_non_http_schemes(self):
        with self.assertRaisesRegex(ValueError, "Local and private network"):
            _validate_public_url("http://localhost")
        with self.assertRaisesRegex(ValueError, "valid HTTP or HTTPS"):
            _validate_public_url("file:///C:/Users/document.pdf")

    def test_pdf_check_rejects_non_pdf_bytes(self):
        with self.assertRaisesRegex(ValueError, "not a valid PDF"):
            extract_pdf(b"not a pdf", "sample.pdf")

    @patch("document_chat.requests.get")
    @patch("document_chat.socket.getaddrinfo")
    def test_url_extraction_keeps_visible_license_notice(self, resolve_host, get_url):
        resolve_host.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 443))
        ]

        response = requests.Response()
        response.status_code = 200
        response.headers = {"content-type": "text/html; charset=utf-8"}
        response.encoding = "utf-8"
        response._content = (
            "<html><title>Example</title><body>Creative Commons license "
            + ("ordinary text " * 7000)
            + "Copyright 2025 self-harm</body></html>"
        ).encode()
        response._content_consumed = True
        get_url.return_value = response
        source = extract_url("https://example.com")

        self.assertIn("Creative Commons", source["content"])
        self.assertIn("Document text truncated", source["content"])
        self.assertEqual(source["title"], "Example")
        self.assertEqual(source["copyright"]["status"], "indicators_found")
        self.assertIn("self-harm related content", source["safetyWarnings"])

    def test_pdf_check_reads_text_from_a_valid_pdf(self):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        pdf = BytesIO()
        writer.write(pdf)

        with self.assertRaisesRegex(ValueError, "No selectable text"):
            extract_pdf(pdf.getvalue(), "blank.pdf")


if __name__ == "__main__":
    unittest.main()
