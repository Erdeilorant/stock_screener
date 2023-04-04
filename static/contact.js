// Get form element and input fields
var contactForm = document.getElementById('contact-form');
var nameInput = document.getElementById('name');
var emailInput = document.getElementById('email');
var messageInput = document.getElementById('message');

// Add form submit event listener
contactForm.addEventListener('Submit', function (event) {
    // Prevent form from submitting
    event.preventDefault();

    // Validate required fields
    if (nameInput.value.trim() === '') {
        alert('Please enter your name.');
        return;
    }
    if (emailInput.value.trim() === '') {
        alert('Please enter your email address.');
        return;
    }
    if (messageInput.value.trim() === '') {
        alert('Please enter your message.');
        return;
    }

    // Submit form if all validation checks pass
    contactForm.submit();
});