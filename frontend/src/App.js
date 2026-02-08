import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { Container } from "react-bootstrap";
import { Outlet } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import GlobalLoader from "./components/GlobalLoader";
import { logout } from "./slices/authSlice";

const App = () => {
  const dispatch = useDispatch();
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("theme");
    return saved === "dark" ? "dark" : "light";
  });

  useEffect(() => {
    const body = document.body;
    if (theme === "dark") {
      body.classList.add("dark-theme");
    } else {
      body.classList.remove("dark-theme");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    const expirationTime = localStorage.getItem("expirationTime");
    if (expirationTime) {
      const currentTime = new Date().getTime();

      if (currentTime > expirationTime) {
        dispatch(logout());
      }
    }
  }, [dispatch]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <div
      className="app-shell"
      style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}
    >
      <GlobalLoader />
      <Header theme={theme} onToggleTheme={toggleTheme} />
      <main className="py-4" style={{ flex: 1 }}>
        <Container className="content-wrapper">
          <Outlet />
        </Container>
      </main>
      <Footer />
    </div>
  );
};

export default App;
