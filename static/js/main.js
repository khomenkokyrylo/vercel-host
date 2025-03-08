// Function to generate a QR code based on provided text
function generateQRCode(text) {
    var qrcodeContainer = document.getElementById("qrcode");
    if (qrcodeContainer) {
        qrcodeContainer.innerHTML = "";
        // QRCode is assumed to be globally available, likely included via a script tag.
        // Ensure QRCode is available. If not, you might need to import it or include it via a script tag.
        if (typeof QRCode !== 'undefined') {
            new QRCode(qrcodeContainer, {
                text: text,
                width: 128,
                height: 128,
            });
        } else {
            console.error("QRCode is not defined. Ensure the library is included.");
            qrcodeContainer.textContent = "QRCode library not found. Please include it in your HTML.";
        }
    }
}

// Mobile menu toggle functionality
document.addEventListener("DOMContentLoaded", function() {
    const mobileMenuButton = document.getElementById("mobile-menu-button");
    const mobileMenu = document.getElementById("mobile-menu");
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener("click", function() {
            mobileMenu.classList.toggle("hidden");
        });
    }
    
    // FAQ Accordion functionality - moved to individual page scripts
    // This prevents conflicts with page-specific implementations
});

// Close modals when clicking outside
window.addEventListener("click", function(event) {
    // Check if there are any open modals and close them if clicking outside
    const openModals = document.querySelectorAll(".modal:not(.hidden)");
    openModals.forEach(modal => {
        if (event.target === modal) {
            modal.classList.add("hidden");
            document.body.style.overflow = "auto"; // Re-enable scrolling
        }
    });
});




// // Function to generate a QR code based on provided text
// function generateQRCode(text) {
//     var qrcodeContainer = document.getElementById("qrcode");
//     if (qrcodeContainer) {
//         qrcodeContainer.innerHTML = "";
//         // QRCode is assumed to be globally available, likely included via a script tag.
//         // If not, you'd need to import it here, e.g., if using a module bundler:
//         // import QRCode from 'qrcode'; 
//         new QRCode(qrcodeContainer, {
//             text: text,
//             width: 128,
//             height: 128,
//         });
//     }
// }

// // FAQ Accordion functionality
// document.addEventListener("DOMContentLoaded", function() {
//     const accordionHeaders = document.querySelectorAll(".accordion-header");
    
//     accordionHeaders.forEach(header => {
//         header.addEventListener("click", function() {
//             // Close all other accordions
//             accordionHeaders.forEach(otherHeader => {
//                 if (otherHeader !== header) {
//                     otherHeader.classList.remove("active");
//                     const otherContent = otherHeader.nextElementSibling;
//                     otherContent.style.maxHeight = null;
//                 }
//             });
            
//             // Toggle this accordion
//             header.classList.toggle("active");
//             const content = header.nextElementSibling;
            
//             if (header.classList.contains("active")) {
//                 content.style.maxHeight = content.scrollHeight + "px";
//             } else {
//                 content.style.maxHeight = null;
//             }
//         });
//     });
// });

// // Mobile menu toggle functionality
// document.addEventListener("DOMContentLoaded", function() {
//     const mobileMenuButton = document.getElementById("mobile-menu-button");
//     const mobileMenu = document.getElementById("mobile-menu");
    
//     if (mobileMenuButton && mobileMenu) {
//         mobileMenuButton.addEventListener("click", function() {
//             mobileMenu.classList.toggle("hidden");
//         });
//     }
// });