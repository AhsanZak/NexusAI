"""A file is kept in the knowledge space the person chose."""

import pytest

from app.documents.extract import UnsupportedFile
from app.knowledge import UnknownSpace, WrongSpaceFile, infer_space, require_file


def test_a_file_name_picks_its_space() -> None:
    assert infer_space("notes.pdf") == "pdf"
    assert infer_space("sales.xlsx") == "excel"
    assert infer_space("rows.csv") == "excel"
    assert infer_space("chart.png") == "image"
    assert infer_space("clip.mp4") == "video"
    assert infer_space("memo.docx") == "document"
    assert infer_space("page.html") == "document"
    assert infer_space("codes.json") == "document"
    assert infer_space("chart.gif") == "image"


def test_a_graph_is_chosen_and_not_guessed_from_the_picture() -> None:
    assert infer_space("chart.png") == "image"
    assert require_file("graph", "chart.png").id == "graph"


def test_the_wrong_kind_of_file_is_refused() -> None:
    with pytest.raises(WrongSpaceFile):
        require_file("pdf", "sales.xlsx")
    with pytest.raises(UnknownSpace):
        require_file("slides", "deck.pdf")
    with pytest.raises(UnsupportedFile):
        infer_space("archive.zip")
