import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Form } from "react-bootstrap";
import { useDispatch, useSelector } from "react-redux";
import Loader from "../components/Loader";

import { useRegister } from "../hooks";
import { setCredentials } from "../slices/authSlice";
import {
  FiUser,
  FiMail,
  FiLock,
  FiUserPlus,
  FiArrowRight,
} from "react-icons/fi";

const RegisterScreen = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { mutate: register, isPending: isLoading } = useRegister();

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

    if (password !== confirmPassword) {
      return;
    } else {
      register(
        { name, email, password },
        {
          onSuccess: (res) => {
            dispatch(setCredentials({ ...res }));
            navigate(redirect);
          },
          onError: () => {},
        },
      );
    }
  };

  return (
    <div className="auth-page fade-in">
      <div className="auth-card">
        <div className="auth-card__header">
          <div className="auth-card__icon">
            <FiUserPlus />
          </div>
          <h1 className="auth-card__title">Create an account</h1>
          <p className="auth-card__subtitle">
            Join us and start shopping today
          </p>
        </div>

        <Form onSubmit={submitHandler} className="auth-card__form">
          <div className="auth-input-group">
            <label className="auth-input-group__label" htmlFor="name">
              Full Name
            </label>
            <div className="auth-input-group__wrapper">
              <FiUser className="auth-input-group__icon" />
              <input
                id="name"
                type="text"
                className="auth-input-group__input"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          </div>

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
                placeholder="Create a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="auth-input-group">
            <label
              className="auth-input-group__label"
              htmlFor="confirmPassword"
            >
              Confirm Password
            </label>
            <div className="auth-input-group__wrapper">
              <FiLock className="auth-input-group__icon" />
              <input
                id="confirmPassword"
                type="password"
                className="auth-input-group__input"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
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
              "Creating account..."
            ) : (
              <>
                Create Account <FiArrowRight />
              </>
            )}
          </button>

          {isLoading && <Loader />}
        </Form>

        <div className="auth-card__footer">
          Already have an account?{" "}
          <Link to={redirect ? `/login?redirect=${redirect}` : "/login"}>
            Sign in <FiArrowRight />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterScreen;
