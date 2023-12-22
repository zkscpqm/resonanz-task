function displayToast(message, color) {
  Toastify({
    text: message,
    duration: 3000,
    close: true,
    gravity: "top",
    position: 'right',
    backgroundColor: color,
    stopOnFocus: true
  }).showToast();
}

export { displayToast };
