'use strict';
const feesPanel = document.getElementById('fees-panel');
document.querySelectorAll('[data-open-fees]').forEach(button => {
  button.addEventListener('click', () => feesPanel.showModal());
});
document.querySelectorAll('[data-close-fees]').forEach(button => {
  button.addEventListener('click', () => feesPanel.close());
});
feesPanel.addEventListener('click', event => {
  const bounds = feesPanel.getBoundingClientRect();
  if (event.target === feesPanel && (event.clientX < bounds.left || event.clientX > bounds.right ||
      event.clientY < bounds.top || event.clientY > bounds.bottom)) feesPanel.close();
});
