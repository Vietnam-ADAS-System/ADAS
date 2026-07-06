import { ThemeProvider } from "./services/theme.jsx";
import { I18nProvider } from "./services/i18n.jsx";
import Dashboard from "./pages/Dashboard.jsx";

export default function App() {
  return (
    <ThemeProvider initialTheme="light">
      <I18nProvider initialLanguage="vi">
        <Dashboard />
      </I18nProvider>
    </ThemeProvider>
  );
}
