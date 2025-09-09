function load_feedback_matching(key, content) {
  load_feedback_code(key, content);
}

function load_input_matching(submissionid, key, input) {
  if (key in input) {
    for (const [i, value] of input[key].entries()) {
      $(".problem select[id='" + key + "_" + i + "']").val(value);
    }
  }
}
