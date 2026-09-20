module.exports = {
  content: ["./templates/**/*.html"],
  // классы статусов приходят из Python (orders/models.py -> status_color)
  safelist: ["text-emerald-500", "text-emerald-600", "text-sky-500", "text-gray-400", "text-red-500"],
  theme: {
    extend: {
      colors: {
        brand: {
          red: '#D80000',
          redHover: '#B00000',
          dark: '#111111',
          bg: '#F7F8FA',
          border: '#E9EBEF'
        }
      },
      fontFamily: { sans: ['Montserrat', 'Inter', 'sans-serif'] }
    }
  },
  plugins: []
}
