from unittest.mock import MagicMock, patch

from tool.read_web_page import (
    ReadWebPageArguments,
    get_read_web_page_message,
    get_read_web_page_permission,
    read_web_page,
)


class TestGetReadWebPageMessage:
    """Tests for the `get_read_web_page_message` function"""

    def test_format(self) -> None:
        """Format the message correctly"""
        arguments: ReadWebPageArguments = {"url": "https://example.com"}
        assert get_read_web_page_message(arguments) == "Reading web site at **https://example.com**"


class TestGetReadWebPagePermission:
    """Tests for the `get_read_web_page_permission` function"""

    def test_auto_approved(self) -> None:
        """Permission should be automatically granted"""
        arguments: ReadWebPageArguments = {"url": "https://example.com"}
        assert get_read_web_page_permission(arguments) is True


class TestReadWebPage:
    """Tests for the `read_web_page` tool"""

    def test_successful_read(self) -> None:
        """Read a web page successfully"""
        url: str = "https://example.com"
        status_code: int = 200
        content_type: str = "text/html"
        extracted_text: str = "Hello world"
        mock_response: MagicMock = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = "<html><body><p>Hello world</p></body></html>"
        mock_response.headers = {"content-type": content_type}
        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get.return_value = mock_response
        with (
            patch("tool.read_web_page.Client", return_value=mock_client_instance),
            patch("tool.read_web_page.extract", return_value=extracted_text),
        ):
            result: str = read_web_page(ReadWebPageArguments(url=url))
        expected_result: str = f'<web_page_read url="{url}">\n<content>\n{extracted_text}\n</content>\n</web_page_read>'
        assert result == expected_result

    def test_non_200_status_code(self) -> None:
        """Read a web page that returns a non-200 status code"""
        url: str = "https://example.com/not-found"
        status_code: int = 404
        mock_response: MagicMock = MagicMock()
        mock_response.status_code = status_code
        mock_response.headers = {"content-type": "text/html"}
        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get.return_value = mock_response
        with patch("tool.read_web_page.Client", return_value=mock_client_instance):
            result: str = read_web_page(ReadWebPageArguments(url=url))
        expected_result: str = f'<web_page_read url="{url}">\n<error>Could not fetch the web page</error>\n<status_code>{status_code}</status_code>\n</web_page_read>'
        assert result == expected_result

    def test_fetch_exception(self) -> None:
        """Read a web page that raises an exception during fetch"""
        url: str = "https://example.com"
        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get.side_effect = Exception("Exception")
        with patch("tool.read_web_page.Client", return_value=mock_client_instance):
            result: str = read_web_page(ReadWebPageArguments(url=url))
        expected_result: str = (
            f'<web_page_read url="{url}">\n<error>Could not fetch the web page</error>\n</web_page_read>'
        )
        assert result == expected_result

    def test_pdf_content_type(self) -> None:
        """Read a web page that returns a PDF content type"""
        url: str = "https://example.com/doc.pdf"
        status_code: int = 200
        content_type: str = "application/pdf"
        mock_response: MagicMock = MagicMock()
        mock_response.status_code = status_code
        mock_response.content = b"%PDF-1.4 fake pdf content"
        mock_response.text = "fake text"
        mock_response.headers = {"content-type": content_type}
        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_pdf_result: str = f'<pdf_document_read location_type="web" location="{url}">\n<note>Redirected from "read_web_page"</note>\n<pages>\n</pages>\n</pdf_document_read>'
        with (
            patch("tool.read_web_page.Client", return_value=mock_client_instance),
            patch("tool.read_web_page.read_pdf_document", return_value=mock_pdf_result),
        ):
            result: str = read_web_page(ReadWebPageArguments(url=url))
        assert result == mock_pdf_result

    def test_extraction_exception(self) -> None:
        """Read a web page whose content cannot be extracted"""
        url: str = "https://example.com"
        status_code: int = 200
        content_type: str = "text/html"
        mock_response: MagicMock = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = "<html></html>"
        mock_response.headers = {"content-type": content_type}
        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get.return_value = mock_response
        with (
            patch("tool.read_web_page.Client", return_value=mock_client_instance),
            patch("tool.read_web_page.extract", side_effect=Exception("Exception")),
        ):
            result: str = read_web_page(ReadWebPageArguments(url=url))
        expected_result: str = f'<web_page_read url="{url}">\n<error>Could not read the web page</error>\n<status_code>{status_code}</status_code>\n<content_type>{content_type}</content_type>\n</web_page_read>'
        assert result == expected_result

    def test_extraction_returns_none(self) -> None:
        """Read a web page whose extraction returns None"""
        url: str = "https://example.com"
        status_code: int = 200
        content_type: str = "text/html"
        mock_response: MagicMock = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = "<html></html>"
        mock_response.headers = {"content-type": content_type}
        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get.return_value = mock_response
        with (
            patch("tool.read_web_page.Client", return_value=mock_client_instance),
            patch("tool.read_web_page.extract", return_value=None),
        ):
            result: str = read_web_page(ReadWebPageArguments(url=url))
        expected_result: str = f'<web_page_read url="{url}">\n<error>Could not read the web page</error>\n<status_code>{status_code}</status_code>\n<content_type>{content_type}</content_type>\n</web_page_read>'
        assert result == expected_result

    def test_extraction_returns_whitespace(self) -> None:
        """Read a web page whose extracted content is only whitespace"""
        url: str = "https://example.com"
        status_code: int = 200
        content_type: str = "text/html"
        mock_response: MagicMock = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = "<html>   </html>"
        mock_response.headers = {"content-type": content_type}
        mock_client_instance: MagicMock = MagicMock()
        mock_client_instance.get.return_value = mock_response
        with (
            patch("tool.read_web_page.Client", return_value=mock_client_instance),
            patch("tool.read_web_page.extract", return_value="   "),
        ):
            result: str = read_web_page(ReadWebPageArguments(url=url))
        expected_result: str = f'<web_page_read url="{url}">\n<error>Could not read the web page</error>\n<status_code>{status_code}</status_code>\n<content_type>{content_type}</content_type>\n</web_page_read>'
        assert result == expected_result
