document.addEventListener("DOMContentLoaded", () => {
    const inputField = document.getElementById("input-show");
    const submitButton = document.getElementById("submit-data");
    const showContainer = document.querySelector(".show-container");
  
    submitButton.addEventListener("click", async () => {
      const eanCode = inputField.value.trim();
      
      if (eanCode) {
        try {
          // Forwards the EAN code
          const response = await fetch("http://127.0.0.1:5000/scrape", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ ean_code: eanCode }),
          });
  
          const data = await response.json();
          
          if (data.error) {
            showContainer.innerHTML = `<p>Error: ${data.error}</p>`;
          } else {
            showContainer.innerHTML = `<p>Search for EAN code ${eanCode} completed successfully.</p>`;
          }
        } catch (error) {
          console.error("Error:", error);
          showContainer.innerHTML = `<p>There was an error processing your request.</p>`;
        }
      } else {
        showContainer.innerHTML = `<p>Please enter an EAN code.</p>`;
      }
    });
  });
  