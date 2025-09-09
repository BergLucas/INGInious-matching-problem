/**
 * Init a matching template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_matching(well, pid, problem) {
  if ("unshuffle" in problem && problem["unshuffle"])
    $("#unshuffle-" + pid, well).attr("checked", true);

  if ("centralize" in problem && problem["centralize"])
    $("#centralize-" + pid, well).attr("checked", true);

  var all_success_feedback = "";
  if ("all_success_feedback" in problem)
    all_success_feedback = problem["all_success_feedback"];

  var partial_success_feedback = "";
  if ("partial_success_feedback" in problem)
    partial_success_feedback = problem["partial_success_feedback"];

  var all_error_feedback = "";
  if ("all_error_feedback" in problem)
    all_error_feedback = problem["all_error_feedback"];

  registerCodeEditor($("#all_success_feedback-" + pid)[0], "rst", 1).setValue(
    all_success_feedback
  );

  registerCodeEditor($("#partial_success_feedback-" + pid)[0], "rst", 1).setValue(
    partial_success_feedback
  );

  registerCodeEditor($("#all_error_feedback-" + pid)[0], "rst", 1).setValue(
    all_error_feedback
  );

  jQuery.each(problem["questions"], function (index, elem) {
    studio_create_matching_question(pid, elem);
  });
}

/**
 * Create a new match in a given matching problem
 * @param pid
 * @param question_data
 */
function studio_create_matching_question(pid, question_data) {
  var well = $(studio_get_problem(pid));

  var index = 0;
  while ($("#question-" + pid + "-" + index).length != 0) index++;

  var row = $("#subproblem_matching_questions").html();
  var new_row_content = row.replace(/PID/g, pid).replace(/QUESTION/g, index);
  var new_row = $("<div></div>")
    .attr("id", "question-" + index + "-" + pid)
    .html(new_row_content);
  $("#questions-" + pid, well).append(new_row);

  if ("question" in question_data) {
    $(".subproblem_matching_question", new_row).val(question_data["question"]);
  }

  if ("answer" in question_data) {
    $(".subproblem_matching_answer", new_row).val(question_data["answer"]);
  }

  var success_feedback = "";
  if ("success_feedback" in question_data) success_feedback = question_data["success_feedback"];

  var error_feedback = "";
  if ("error_feedback" in question_data) error_feedback = question_data["error_feedback"];

  registerCodeEditor(
    $(".subproblem_matching_success_feedback", new_row)[0],
    "rst",
    1
  ).setValue(success_feedback);

  registerCodeEditor(
    $(".subproblem_matching_error_feedback", new_row)[0],
    "rst",
    1
  ).setValue(error_feedback);
}

/**
 * Delete a matching question
 * @param pid
 * @param question
 */
function studio_delete_matching_question(pid, question) {
  $("#question-" + question + "-" + pid).detach();
}
