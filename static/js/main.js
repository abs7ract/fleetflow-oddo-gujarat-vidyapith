// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. Trip Dispatcher Validation Logic ---
    const dispatchForm = document.getElementById('dispatch-form');
    
    if (dispatchForm) {
        dispatchForm.addEventListener('submit', function(e) {
            const vehicleSelect = document.getElementById('vehicle-select');
            const cargoWeightInput = document.getElementById('cargo-weight');
            
            // Extract the max capacity from the selected option's data attribute
            // (You will need to pass this data attribute in your HTML, e.g., data-capacity="500")
            const selectedOption = vehicleSelect.options[vehicleSelect.selectedIndex];
            const maxCapacity = parseFloat(selectedOption.getAttribute('data-capacity'));
            const enteredWeight = parseFloat(cargoWeightInput.value);

            // Validation Rule: Check if CargoWeight > MaxCapacity
            if (enteredWeight > maxCapacity) {
                e.preventDefault(); // Stop the form from submitting
                alert(`Validation Failed: Cargo weight (${enteredWeight}kg) exceeds the vehicle's maximum capacity (${maxCapacity}kg).`);
                
                // Add a red border to highlight the error to the user
                cargoWeightInput.classList.add('border-red-500', 'focus:ring-red-500');
            } else {
                // Remove error styling if it passes
                cargoWeightInput.classList.remove('border-red-500', 'focus:ring-red-500');
            }
        });
    }

    // --- 2. Print/Export PDF Mock Function for Analytics Page ---
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            alert('Generating PDF Export... (Hackathon Mock)');
            window.print(); // Quick hackathon trick to open the browser's PDF print dialog
        });
    }
});