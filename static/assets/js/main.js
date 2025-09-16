document.addEventListener("DOMContentLoaded", function() {
    const productCards = document.querySelectorAll('.product-card');

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = `fadeInUp 0.5s ease-out forwards`;
            }
        });
    }, {
        threshold: 0.1
    });

    productCards.forEach(card => {
        observer.observe(card);
    });
});

// Add this to your CSS file for the animation
/*
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
*/
// --- Image Gallery Functionality ---
function changeImage(imageSrc) {
    // Set the main image source to the clicked thumbnail's source
    document.getElementById('mainImage').src = imageSrc;

    // Update active state for thumbnails
    const thumbnails = document.querySelectorAll('.thumbnail');
    thumbnails.forEach(thumb => {
        // If thumb src matches the new main image src, add 'active' class
        if (thumb.src.includes(imageSrc)) {
            thumb.classList.add('active');
        } else {
            thumb.classList.remove('active');
        }
    });
}


// --- Accordion Functionality ---
document.addEventListener('DOMContentLoaded', function () {
    const accordionHeaders = document.querySelectorAll('.accordion-header');

    accordionHeaders.forEach(header => {
        header.addEventListener('click', function () {
            const content = this.nextElementSibling;
            
            // Toggle the content's visibility
            if (content.style.maxHeight) {
                content.style.maxHeight = null;
            } else {
                content.style.maxHeight = content.scrollHeight + "px";
            }
        });
    });

    // --- Size Selector Functionality ---
    const sizeOptions = document.querySelectorAll('.size-option');
    sizeOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Remove 'active' style from all options
            sizeOptions.forEach(opt => opt.style.borderColor = '#ccc');
            // Add 'active' style to the clicked option
            if (!this.disabled) {
                this.style.borderColor = '#111';
            }
        });
    });
});





