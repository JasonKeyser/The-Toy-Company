document.addEventListener('focusin', function (e) {
  if (e.target.matches('input[type="number"]')) {
    e.target.select();
  }
});