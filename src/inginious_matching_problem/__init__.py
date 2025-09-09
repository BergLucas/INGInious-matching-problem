from __future__ import annotations

import os
from collections import defaultdict
from hashlib import sha256
from random import Random
from typing import TYPE_CHECKING, Any

from flask import Response, send_from_directory
from inginious.common.tasks_problems import Problem
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.parsable_text import ParsableText
from inginious.frontend.task_problems import DisplayableProblem

if TYPE_CHECKING:
    from gettext import NullTranslations

    from inginious.client.client import Client
    from inginious.common.filesystems import FileSystemProvider
    from inginious.frontend.course_factory import CourseFactory
    from inginious.frontend.plugin_manager import PluginManager
    from inginious.frontend.task_factory import TaskFactory
    from inginious.frontend.template_helper import TemplateHelper


__version__ = "0.1.0"

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")


MIN_QUESTION_NUMBER = 3


class MatchingProblemStatic(INGIniousPage):
    """Serve static files for the matching plugin."""

    def GET(self, path: str) -> Response:  # noqa: N802
        """Serve static files for the matching plugin.

        Args:
            path: The path to the static file.

        Returns:
            The static file.
        """
        return send_from_directory(os.path.join(PATH_TO_PLUGIN, "static"), path)


class MatchingProblem(Problem):
    """Display a list of questions which must be correctly matched a list of answers."""  # noqa: E501

    def __init__(
        self,
        problemid: str,
        content: dict[str, Any],
        translations: dict[str, NullTranslations],
        taskfs: FileSystemProvider,
    ) -> None:
        """Initialises a MatchingProblem.

        Args:
            problemid: The problem ID.
            content: The problem content.
            translations: The problem translations.
            taskfs: The task file system provider.
        """
        if "questions" not in content:
            raise Exception(f"Problem {problemid} requires a questions field")

        if len({question["question"] for question in content["questions"]}) != len(
            content["questions"]
        ):
            raise Exception(f"All questions in problem {problemid} must be different")

        if len(content["questions"]) < MIN_QUESTION_NUMBER:
            raise Exception(
                f"Problem {problemid} requires at least {MIN_QUESTION_NUMBER} questions"
            )

        super().__init__(problemid, content, translations, taskfs)
        self._header = content.get("header", "")
        self._unshuffle = content.get("unshuffle", False)
        self._centralize = "centralize" in content
        self._all_success_feedback = content.get("all_success_feedback")
        self._partial_success_feedback = content.get("partial_success_feedback")
        self._all_error_feedback = content.get("all_error_feedback")
        self._questions: list[dict] = list(content["questions"])

    @classmethod
    def get_type(cls) -> str:  # type: ignore
        """Returns the type of the problem.

        Returns:
            The type of the problem.
        """
        return "matching"

    def input_is_consistent(  # type: ignore
        self,
        task_input: dict[str, Any],
        default_allowed_extension: str,
        default_max_size: int,
    ) -> bool:
        """Checks if the input is consistent.

        Args:
            task_input: The task input.
            default_allowed_extension: The default allowed file extension.
            default_max_size: The default maximum file size.

        Returns:
            True if the input is consistent, False otherwise.
        """
        pid = self.get_id()
        answer_hashes = {
            self.get_answer_hash(question["answer"]) for question in self._questions
        }
        return pid in task_input and all(
            answer_hash in answer_hashes for answer_hash in task_input[pid]
        )

    def get_answer_hash(self, answer: str) -> str:
        """Gets the hash of the answer.

        Args:
            answer: The answer

        Returns:
            The hash of the answer
        """
        return sha256(answer.encode()).hexdigest()

    def input_type(self) -> type:
        """Returns the type of the input.

        Returns:
            The type of the input.
        """
        return list

    def check_answer(  # type: ignore  # noqa: D102
        self,
        task_input: dict[str, Any],
        language: str,
    ) -> tuple[bool, str | None, list[str] | None, int, str]:
        feedbacks: list[str] = []
        invalid_count = 0

        question_ids: dict[str, set[int]] = defaultdict(set)
        for i, question in enumerate(self._questions):
            question_ids[self.get_answer_hash(question["answer"])].add(i)

        for i, answer_hash in enumerate(task_input[self.get_id()]):
            if i in question_ids[answer_hash]:
                feedbacks.append(self._questions[i]["success_feedback"])
            else:
                invalid_count += 1
                feedbacks.append(self._questions[i]["error_feedback"])

        if invalid_count == 0:
            global_message = self._all_success_feedback
            valid = True
        elif invalid_count < len(self._questions):
            global_message = self._partial_success_feedback
            valid = False
        else:
            global_message = self._all_error_feedback
            valid = False

        if global_message is not None:
            feedbacks.insert(0, global_message)

        return (
            valid,
            None,
            feedbacks if not self._centralize and feedbacks else None,
            invalid_count,
            "",
        )

    @classmethod
    def parse_problem(cls, problem_content: dict[str, Any]) -> dict[str, Any]:
        """Parses the problem content.

        Args:
            problem_content: The problem content.

        Returns:
            The parsed problem.
        """
        if "unshuffle" in problem_content:
            problem_content["unshuffle"] = True

        if "centralize" in problem_content:
            problem_content["centralize"] = True

        if (
            "all_success_feedback" in problem_content
            and problem_content["all_success_feedback"].strip() == ""
        ):
            del problem_content["all_success_feedback"]

        if (
            "partial_success_feedback" in problem_content
            and problem_content["partial_success_feedback"].strip() == ""
        ):
            del problem_content["partial_success_feedback"]

        if (
            "all_error_feedback" in problem_content
            and problem_content["all_error_feedback"].strip() == ""
        ):
            del problem_content["all_error_feedback"]

        if "questions" in problem_content:
            problem_content["questions"] = [
                val
                for _, val in sorted(
                    iter(problem_content["questions"].items()), key=lambda x: int(x[0])
                )
            ]
            for match in problem_content["questions"]:
                for key in ("question", "answer", "success_feedback", "error_feedback"):
                    if key in match and match[key].strip() == "":
                        del match[key]

        return Problem.parse_problem(problem_content)

    @classmethod
    def get_text_fields(cls) -> dict[str, Any]:  # noqa: D102
        fields: dict[str, Any] = Problem.get_text_fields()
        fields.update(
            {
                "header": True,
                "success_feedback": True,
                "partial_success_feedback": True,
                "error_feedback": True,
                "questions": [
                    {
                        "question": True,
                        "answer": True,
                        "success_feedback": True,
                        "error_feedback": True,
                    }
                ],
            },
        )
        return fields


class MatchingDisplayableProblem(MatchingProblem, DisplayableProblem):  # type: ignore
    """A displayable matching problem."""

    def __init__(
        self,
        problemid: str,
        content: dict[str, Any],
        translations: dict[str, NullTranslations],
        taskfs: FileSystemProvider,
    ) -> None:
        """Initialises a MatchingDisplayableProblem.

        Args:
            problemid: The problem ID.
            content: The problem content.
            translations: The problem translations.
            taskfs: The task file system provider.
        """
        super().__init__(problemid, content, translations, taskfs)

    @classmethod
    def get_type_name(cls, language: str) -> str:  # type: ignore
        """Returns the type name of the problem.

        Args:
            language: The language code.

        Returns:
            The type name of the problem.
        """
        return "matching"

    def show_input(  # type: ignore  # noqa: D415
        self,
        template_helper: TemplateHelper,
        language: str,
        seed: int,
    ) -> str:
        """Show a MatchingDisplayableProblem.

        Args:
            template_helper: The template helper instance.
            language: The language code.
            seed: The random seed.

        Returns:
            The rendered input HTML.
        """
        answers = [question["answer"] for question in self._questions]

        if not self._unshuffle:
            Random("{}#{}#{}".format(self.get_id(), language, seed)).shuffle(answers)  # noqa: S311

        header = ParsableText(
            self.gettext(language, self._header),
            "rst",
            translation=self.get_translation_obj(language),
        )
        return template_helper.render(
            "tasks/matching.html",
            template_folder=PATH_TO_TEMPLATES,
            pid=self.get_id(),
            header=header,
            questions=self._questions,
            answers=answers,
            answer_hash=self.get_answer_hash,
            display=lambda text: ParsableText(
                self.gettext(language, text) if text else "",
                "rst",
                translation=self.get_translation_obj(language),
            ),
        )

    @classmethod
    def show_editbox(  # type: ignore
        cls,
        template_helper: TemplateHelper,
        key: str,
        language: str,
    ) -> str:
        """Show the edit box for a MatchingDisplayableProblem.

        Args:
            template_helper: The template helper instance.
            key: The problem key.
            language: The language code.

        Returns:
            The rendered edit box HTML.
        """
        return template_helper.render(
            "course_admin/subproblems/matching.html",
            template_folder=PATH_TO_TEMPLATES,
            key=key,
        )

    @classmethod
    def show_editbox_templates(  # type: ignore
        cls,
        template_helper: TemplateHelper,
        key: str,
        language: str,
    ) -> str:
        """Show the edit box templates for a MatchingDisplayableProblem.

        Args:
            template_helper: The template helper instance.
            key: The problem key.
            language: The language code.

        Returns:
            The rendered edit box templates HTML.
        """
        return template_helper.render(
            "course_admin/subproblems/matching_templates.html",
            template_folder=PATH_TO_TEMPLATES,
            key=key,
        )


def init(
    plugin_manager: PluginManager,
    course_factory: CourseFactory,
    client: Client,
    plugin_config: dict[str, Any],
) -> None:
    """Initialises the matching-problem plugin.

    Args:
        plugin_manager: The plugin manager instance.
        course_factory: The course factory instance.
        client: The client instance.
        plugin_config: The plugin configuration dictionary.
    """
    plugin_manager.add_page(
        "/plugins/matching/static/<path:path>",
        MatchingProblemStatic.as_view("matching_static"),
    )
    plugin_manager.add_hook(
        "javascript_header",
        lambda: "/plugins/matching/static/js/studio.js",
    )
    plugin_manager.add_hook(
        "javascript_header",
        lambda: "/plugins/matching/static/js/task.js",
    )
    plugin_manager.add_hook(
        "css",
        lambda: "/plugins/matching/static/css/style.css",
    )
    task_factory: TaskFactory = course_factory.get_task_factory()
    task_factory.add_problem_type(MatchingDisplayableProblem)
