function updateStatus() {
  fetch('/current_status')
      .then(response => response.json())
      .then(data => {
          document.getElementById('current-number').innerText = data.current_number;
          document.getElementById('queue-length').innerText = data.queue_length;
          document.getElementById('wait-time').innerText = data.average_wait_time;
      });
}

setInterval(updateStatus, 5000);
