import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Form } from "react-bootstrap";
import { useDispatch, useSelector } from "react-redux";
import Loader from "../components/Loader";

import { useLogin } from "../hooks";
import { setCredentials } from "../slices/authSlice";
import { FiMail, FiLock, FiLogIn, FiArrowRight } from "react-icons/fi";

const LoginScreen = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { mutate: login, isPending: isLoading } = useLogin();
  const { userInfo } = useSelector((state) => state.auth);

  const { search } = useLocation();
  const sp = new URLSearchParams(search);
  const redirect = sp.get("redirect") || "/";

  useEffect(() => {
    if (userInfo) {
      navigate(redirect);
    }
  }, [navigate, redirect, userInfo]);

  const submitHandler = async (e) => {
    e.preventDefault();

    login(
      { email, password },
      {
        onSuccess: (res) => {
          dispatch(setCredentials({ ...res }));
          navigate(redirect);
        },
        onError: () => {},
      },
    );
  };

  return (
    <div className="auth-page fade-in">
      <div className="auth-card">
        <div className="auth-card__header">
          <div className="auth-card__icon">
            <FiLogIn />
          </div>
          <h1 className="auth-card__title">Welcome back</h1>
          <p className="auth-card__subtitle">
            Sign in to your account to continue
          </p>
        </div>

        <Form onSubmit={submitHandler} className="auth-card__form">
          <div className="auth-input-group">
            <label className="auth-input-group__label" htmlFor="email">
              Email Address
            </label>
            <div className="auth-input-group__wrapper">
              <FiMail className="auth-input-group__icon" />
              <input
                id="email"
                type="email"
                className="auth-input-group__input"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="auth-input-group">
            <label className="auth-input-group__label" htmlFor="password">
              Password
            </label>
            <div className="auth-input-group__wrapper">
              <FiLock className="auth-input-group__icon" />
              <input
                id="password"
                type="password"
                className="auth-input-group__input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button
            className="auth-card__submit"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? (
              "Signing in..."
            ) : (
              <>
                Sign In <FiArrowRight />
              </>
            )}
          </button>

          {isLoading && <Loader />}
        </Form>

        <div className="auth-card__footer">
          New customer?{" "}
          <Link to={redirect ? `/register?redirect=${redirect}` : "/register"}>
            Create an account <FiArrowRight />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;
