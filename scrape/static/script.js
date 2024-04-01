document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("urlForm").onsubmit = function() {
      document.getElementById("feedback").innerHTML = "Processing... Please wait.";
    };
  });
  