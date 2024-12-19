// Constants
const MAX_FUNDING = 10000000; // $1e0M maximum funding
const CURRENT_FUNDING = 5200000; // $5.2M current funding (static for demo)
const GRADIENT_COLORS = {
    start: '#4ECDC4',
    middle: '#45B7AC',
    end: '#3C9E94'
};

// DOM Elements
const currentAmount = document.getElementById('currentAmount');
const percentageComplete = document.getElementById('percentageComplete');
const eggShape = document.getElementById('eggShape');

// Utility Functions
const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
        notation: 'compact',
        compactDisplay: 'short'
    }).format(amount);
};

const calculatePercentage = (amount) => {
    return Math.min((amount / MAX_FUNDING) * 100, 100);
};

const updateGradient = (percentage) => {
    const { start, middle, end } = GRADIENT_COLORS;
    return `linear-gradient(to bottom, 
        ${start} 0%, 
        ${middle} ${percentage}%, 
        ${end} 100%)`;
};

// Initialize
const initializeApp = () => {
    const percentage = calculatePercentage(CURRENT_FUNDING);
    
    // Update display values
    currentAmount.textContent = formatCurrency(CURRENT_FUNDING);
    percentageComplete.textContent = `${Math.round(percentage)}%`;
    
    // Update egg visualization
    eggShape.style.fill = updateGradient(percentage);
};

// Start the application
document.addEventListener('DOMContentLoaded', initializeApp);