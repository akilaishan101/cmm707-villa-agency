(function () {
  const form = document.getElementById("enquiry-form");

  if (!form) {
    return;
  }

  const submitButton = document.getElementById("form-submit");
  const statusMessage = document.getElementById("form-status");
  const propertyIdInput = document.getElementById("property-id");
  const viewingDateInput = document.getElementById("viewing-datetime");
  const parameters = new URLSearchParams(window.location.search);
  const requestedPropertyId = Number(parameters.get("property_id"));

  if (requestedPropertyId > 0) {
    propertyIdInput.value = requestedPropertyId;
  }

  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  viewingDateInput.min = now.toISOString().slice(0, 16);

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    submitButton.disabled = true;
    statusMessage.style.color = "#555";
    statusMessage.textContent = "Submitting your visit request...";

    const payload = {
      property_id: Number(propertyIdInput.value),
      customer_name: document.getElementById("customer-name").value.trim(),
      customer_email: document.getElementById("customer-email").value.trim(),
      customer_contact: document.getElementById("customer-contact").value.trim(),
      viewing_datetime: new Date(viewingDateInput.value).toISOString(),
      message: document.getElementById("message").value.trim(),
      status: "Pending",
    };

    try {
      const response = await fetch("/enquiries", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("The enquiry service rejected the request.");
      }

      const enquiry = await response.json();
      form.reset();
      propertyIdInput.value = requestedPropertyId > 0 ? requestedPropertyId : 1;
      statusMessage.style.color = "#198754";
      statusMessage.textContent = `Visit scheduled successfully. Enquiry #${enquiry.enquiry_id}.`;
    } catch (error) {
      statusMessage.style.color = "#dc3545";
      statusMessage.textContent = error.message;
    } finally {
      submitButton.disabled = false;
    }
  });
})();
