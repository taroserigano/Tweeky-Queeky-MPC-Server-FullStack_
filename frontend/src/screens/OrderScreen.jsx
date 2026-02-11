import { useEffect, useState, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { PayPalButtons, usePayPalScriptReducer } from "@paypal/react-paypal-js";
import { loadStripe } from "@stripe/stripe-js";
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";
import { useSelector } from "react-redux";
import {
  FiPackage,
  FiTruck,
  FiCreditCard,
  FiCheckCircle,
  FiClock,
  FiMapPin,
  FiMail,
  FiUser,
  FiCopy,
  FiShoppingBag,
  FiEdit3,
  FiSave,
} from "react-icons/fi";
import { PageLoader } from "../components/Loader";
import { getErrorMessage } from "../utils/errorUtils";
import {
  useOrderDetails,
  usePayOrder,
  usePayPalClientId,
  useDeliverOrder,
  useStripePublishableKey,
  useCreatePaymentIntent,
  useUpdateOrder,
} from "../hooks/useOrderQueries";

/* ─────────────────────────────────────────────────────────────
   Styles
───────────────────────────────────────────────────────────── */
const styles = {
  container: {
    maxWidth: "1200px",
    margin: "0 auto",
    padding: "24px 16px",
  },
  header: {
    marginBottom: "32px",
  },
  orderIdContainer: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    flexWrap: "wrap",
  },
  orderTitle: {
    fontSize: "14px",
    fontWeight: "500",
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    margin: 0,
  },
  orderId: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    background: "var(--bg-muted)",
    padding: "8px 16px",
    borderRadius: "8px",
    fontFamily: "monospace",
    fontSize: "14px",
    color: "var(--text-primary)",
  },
  copyBtn: {
    background: "none",
    border: "none",
    cursor: "pointer",
    color: "var(--text-muted)",
    padding: "4px",
    borderRadius: "4px",
    display: "flex",
    alignItems: "center",
    transition: "all 0.2s",
  },
  statusTimeline: {
    display: "flex",
    gap: "8px",
    marginTop: "20px",
    flexWrap: "wrap",
  },
  statusBadge: (isActive, isSuccess) => ({
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "8px 16px",
    borderRadius: "50px",
    fontSize: "13px",
    fontWeight: "500",
    background: isSuccess ? "#dcfce7" : isActive ? "#fef3c7" : "#f1f5f9",
    color: isSuccess ? "#166534" : isActive ? "#92400e" : "#64748b",
    border: `1px solid ${isSuccess ? "#bbf7d0" : isActive ? "#fde68a" : "#e2e8f0"}`,
  }),
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: "24px",
  },
  mainContent: {
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },
  card: {
    background: "var(--bg-surface)",
    borderRadius: "16px",
    border: "1px solid var(--border-color)",
    overflow: "hidden",
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "20px 24px",
    borderBottom: "1px solid var(--border-color)",
    background: "var(--bg-muted)",
  },
  cardIcon: {
    width: "40px",
    height: "40px",
    borderRadius: "10px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "18px",
  },
  cardTitle: {
    fontSize: "16px",
    fontWeight: "600",
    color: "var(--text-primary)",
    margin: 0,
  },
  cardBody: {
    padding: "24px",
  },
  infoGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "20px",
  },
  infoItem: {
    display: "flex",
    alignItems: "flex-start",
    gap: "12px",
  },
  infoIcon: {
    width: "36px",
    height: "36px",
    borderRadius: "8px",
    background: "var(--bg-muted)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "var(--text-muted)",
    flexShrink: 0,
  },
  infoLabel: {
    fontSize: "12px",
    color: "var(--text-muted)",
    marginBottom: "2px",
  },
  infoValue: {
    fontSize: "14px",
    fontWeight: "500",
    color: "var(--text-primary)",
    margin: 0,
  },
  addressBox: {
    background: "var(--bg-muted)",
    borderRadius: "12px",
    padding: "16px",
    marginTop: "16px",
  },
  addressText: {
    fontSize: "14px",
    color: "var(--text-secondary)",
    lineHeight: "1.6",
    margin: 0,
  },
  editBtn: {
    background: "none",
    border: "1px solid var(--border-color)",
    borderRadius: "8px",
    padding: "6px 12px",
    fontSize: "13px",
    fontWeight: "500",
    color: "#3b82f6",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    marginLeft: "auto",
    transition: "all 0.2s",
  },
  formInput: {
    width: "100%",
    padding: "10px 14px",
    border: "1px solid var(--border-color)",
    borderRadius: "8px",
    fontSize: "14px",
    color: "var(--text-primary)",
    background: "var(--bg-surface)",
    outline: "none",
    transition: "border-color 0.2s",
    marginBottom: "8px",
  },
  formLabel: {
    fontSize: "12px",
    fontWeight: "500",
    color: "var(--text-muted)",
    marginBottom: "4px",
    display: "block",
  },
  formRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "12px",
  },
  radioGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  radioOption: (isSelected) => ({
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "14px 16px",
    borderRadius: "10px",
    border: isSelected
      ? "2px solid var(--primary-500)"
      : "1px solid var(--border-color)",
    background: isSelected ? "rgba(59, 130, 246, 0.15)" : "var(--bg-muted)",
    cursor: "pointer",
    transition: "all 0.2s",
  }),
  radioCircle: (isSelected) => ({
    width: "18px",
    height: "18px",
    borderRadius: "50%",
    border: isSelected
      ? "5px solid var(--primary-500)"
      : "2px solid var(--border-medium)",
    transition: "all 0.2s",
    flexShrink: 0,
  }),
  radioLabel: {
    fontSize: "14px",
    fontWeight: "500",
    color: "var(--text-primary)",
  },
  orderItem: {
    display: "flex",
    gap: "16px",
    padding: "16px 0",
    borderBottom: "1px solid var(--border-color)",
  },
  itemImage: {
    width: "80px",
    height: "80px",
    borderRadius: "12px",
    objectFit: "cover",
    background: "var(--bg-muted)",
    border: "1px solid var(--border-color)",
  },
  itemDetails: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
  },
  itemName: {
    fontSize: "15px",
    fontWeight: "500",
    color: "var(--text-primary)",
    textDecoration: "none",
    marginBottom: "4px",
    display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
  },
  itemMeta: {
    fontSize: "13px",
    color: "var(--text-muted)",
  },
  itemPrice: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
    justifyContent: "center",
  },
  priceMain: {
    fontSize: "16px",
    fontWeight: "600",
    color: "var(--text-primary)",
  },
  priceCalc: {
    fontSize: "12px",
    color: "var(--text-muted)",
  },
  sidebar: {
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },
  summaryCard: {
    background: "linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)",
    borderRadius: "16px",
    padding: "24px",
    color: "#fff",
  },
  summaryTitle: {
    fontSize: "18px",
    fontWeight: "600",
    marginBottom: "20px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  summaryRow: {
    display: "flex",
    justifyContent: "space-between",
    padding: "12px 0",
    borderBottom: "1px solid rgba(255,255,255,0.15)",
    fontSize: "14px",
  },
  summaryLabel: {
    color: "rgba(255,255,255,0.8)",
  },
  summaryValue: {
    fontWeight: "500",
  },
  summaryTotal: {
    display: "flex",
    justifyContent: "space-between",
    padding: "16px 0 0",
    fontSize: "20px",
    fontWeight: "700",
  },
  paymentCard: {
    background: "var(--bg-surface)",
    borderRadius: "16px",
    border: "1px solid var(--border-color)",
    padding: "24px",
  },
  paymentTitle: {
    fontSize: "16px",
    fontWeight: "600",
    color: "var(--text-primary)",
    marginBottom: "16px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  adminBtn: {
    width: "100%",
    padding: "14px 24px",
    background: "linear-gradient(135deg, #059669 0%, #10b981 100%)",
    color: "#fff",
    border: "none",
    borderRadius: "12px",
    fontSize: "15px",
    fontWeight: "600",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    transition: "all 0.2s",
    marginTop: "16px",
  },
  errorContainer: {
    minHeight: "400px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    textAlign: "center",
    padding: "40px",
  },
  errorIcon: {
    width: "64px",
    height: "64px",
    borderRadius: "50%",
    background: "#fef2f2",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#ef4444",
    fontSize: "28px",
    marginBottom: "16px",
  },
  errorTitle: {
    fontSize: "18px",
    fontWeight: "600",
    color: "#1e293b",
    marginBottom: "8px",
  },
  errorText: {
    fontSize: "14px",
    color: "#64748b",
  },
};

/* ─────────────────────────────────────────────────────────────
   Media Query Styles (applied via className)
───────────────────────────────────────────────────────────── */
const responsiveStyles = `
  @media (min-width: 1024px) {
    .order-grid {
      grid-template-columns: 1fr 380px !important;
    }
  }
`;

/* ─────────────────────────────────────────────────────────────
   Stripe Checkout Form (rendered inside <Elements>)
───────────────────────────────────────────────────────────── */
const StripeCheckoutForm = ({ orderId, onSuccess }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;

    setProcessing(true);
    const { error, paymentIntent } = await stripe.confirmPayment({
      elements,
      redirect: "if_required",
    });

    if (error) {
      setProcessing(false);
    } else if (paymentIntent && paymentIntent.status === "succeeded") {
      onSuccess({
        id: paymentIntent.id,
        status: "COMPLETED",
        update_time: new Date().toISOString(),
        source: "stripe",
        paymentIntentId: paymentIntent.id,
      });
      setProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <PaymentElement />
      <button
        type="submit"
        disabled={!stripe || processing}
        style={{
          width: "100%",
          marginTop: "16px",
          padding: "14px 24px",
          background: processing
            ? "var(--text-muted)"
            : "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
          color: "#fff",
          border: "none",
          borderRadius: "12px",
          fontSize: "15px",
          fontWeight: "600",
          cursor: processing ? "not-allowed" : "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
        }}
      >
        {processing ? (
          <>
            <span className="spinner-border spinner-border-sm" role="status" />
            Processing…
          </>
        ) : (
          <>
            <FiCreditCard />
            Pay Now
          </>
        )}
      </button>
    </form>
  );
};

/* ─────────────────────────────────────────────────────────────
   Stripe Wrapper – loads publishable key + creates PaymentIntent
───────────────────────────────────────────────────────────── */
const StripePaymentWrapper = ({ orderId, onSuccess }) => {
  const { data: stripeConfig, isLoading: loadingKey } =
    useStripePublishableKey();
  const { mutate: createIntent, isLoading: creatingIntent } =
    useCreatePaymentIntent();

  const [clientSecret, setClientSecret] = useState(null);
  const [stripePromise, setStripePromise] = useState(null);

  // Load publishable key
  useEffect(() => {
    if (stripeConfig?.publishableKey) {
      setStripePromise(loadStripe(stripeConfig.publishableKey));
    }
  }, [stripeConfig]);

  // Create Payment Intent
  useEffect(() => {
    if (stripePromise && !clientSecret) {
      createIntent(orderId, {
        onSuccess: (data) => setClientSecret(data.clientSecret),
        onError: () => {},
      });
    }
  }, [stripePromise, clientSecret, orderId, createIntent]);

  if (loadingKey || creatingIntent || !stripePromise || !clientSecret) {
    return (
      <div style={{ textAlign: "center", padding: "20px" }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading Stripe...</span>
        </div>
      </div>
    );
  }

  return (
    <Elements stripe={stripePromise} options={{ clientSecret }}>
      <StripeCheckoutForm orderId={orderId} onSuccess={onSuccess} />
    </Elements>
  );
};

/* ─────────────────────────────────────────────────────────────
   Component
───────────────────────────────────────────────────────────── */
const OrderScreen = () => {
  const { id: orderId } = useParams();

  const { data: order, refetch, isLoading, error } = useOrderDetails(orderId);
  const { mutate: payOrder, isLoading: loadingPay } = usePayOrder();
  const { mutate: deliverOrder, isLoading: loadingDeliver } = useDeliverOrder();
  const { mutate: updateOrder, isLoading: loadingUpdate } = useUpdateOrder();
  const { userInfo } = useSelector((state) => state.auth);
  const [{ isPending }, paypalDispatch] = usePayPalScriptReducer();
  const {
    data: paypal,
    isLoading: loadingPayPal,
    error: errorPayPal,
  } = usePayPalClientId();

  // Editable address state
  const [editingAddress, setEditingAddress] = useState(false);
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [country, setCountry] = useState("");

  // Sync address state when order loads
  useEffect(() => {
    if (order && order.shippingAddress) {
      setAddress(order.shippingAddress.address || "");
      setCity(order.shippingAddress.city || "");
      setPostalCode(order.shippingAddress.postalCode || "");
      setCountry(order.shippingAddress.country || "");
    }
  }, [order]);

  const saveAddress = useCallback(() => {
    if (!address || !city || !postalCode || !country) {
      return;
    }
    updateOrder(
      {
        orderId,
        updateData: {
          shippingAddress: { address, city, postalCode, country },
        },
      },
      {
        onSuccess: () => {
          refetch();
          setEditingAddress(false);
        },
        onError: () => {},
      },
    );
  }, [address, city, postalCode, country, orderId, updateOrder, refetch]);

  const handlePaymentMethodChange = useCallback(
    (method) => {
      updateOrder(
        {
          orderId,
          updateData: { paymentMethod: method },
        },
        {
          onSuccess: () => {
            refetch();
          },
          onError: () => {},
        },
      );
    },
    [orderId, updateOrder, refetch],
  );

  useEffect(() => {
    if (!errorPayPal && !loadingPayPal && paypal?.clientId) {
      const loadPaypalScript = async () => {
        paypalDispatch({
          type: "resetOptions",
          value: {
            "client-id": paypal.clientId,
            currency: "USD",
          },
        });
        paypalDispatch({ type: "setLoadingStatus", value: "pending" });
      };
      if (order && !order.isPaid) {
        if (!window.paypal) {
          loadPaypalScript();
        }
      }
    }
  }, [errorPayPal, loadingPayPal, order, paypal, paypalDispatch]);

  const copyOrderId = () => {
    navigator.clipboard.writeText(order._id);
  };

  function onApprove(data, actions) {
    return actions.order.capture().then(async function (details) {
      payOrder(
        { orderId, details },
        {
          onSuccess: () => {
            refetch();
          },
          onError: () => {},
        },
      );
    });
  }

  function onError(err) {}

  function createOrder(data, actions) {
    return actions.order
      .create({
        purchase_units: [
          {
            amount: { value: order.totalPrice },
          },
        ],
      })
      .then((orderID) => orderID);
  }

  const deliverHandler = async () => {
    deliverOrder(orderId, {
      onSuccess: () => {
        refetch();
      },
      onError: () => {},
    });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Loading state
  if (isLoading) {
    return <PageLoader text="Loading order details..." />;
  }

  // Error state
  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.errorContainer}>
          <div style={styles.errorIcon}>
            <FiPackage />
          </div>
          <h2 style={styles.errorTitle}>Order Not Found</h2>
          <p style={styles.errorText}>
            {getErrorMessage(error, "Unable to load order details")}
          </p>
          <Link
            to="/"
            style={{
              marginTop: "16px",
              color: "#3b82f6",
              textDecoration: "none",
              fontWeight: "500",
            }}
          >
            ← Return to Shop
          </Link>
        </div>
      </div>
    );
  }

  return (
    <>
      <style>{responsiveStyles}</style>
      <div style={styles.container}>
        {/* Header */}
        <header style={styles.header}>
          <p style={styles.orderTitle}>Order Confirmation</p>
          <div style={styles.orderIdContainer}>
            <div style={styles.orderId}>
              <FiPackage />
              <span>{order._id}</span>
              <button
                style={styles.copyBtn}
                onClick={copyOrderId}
                title="Copy Order ID"
              >
                <FiCopy size={14} />
              </button>
            </div>
          </div>

          {/* Status Timeline */}
          <div style={styles.statusTimeline}>
            <span style={styles.statusBadge(true, true)}>
              <FiCheckCircle size={14} />
              Order Placed
            </span>
            <span style={styles.statusBadge(true, order.isPaid)}>
              {order.isPaid ? (
                <FiCheckCircle size={14} />
              ) : (
                <FiClock size={14} />
              )}
              {order.isPaid
                ? `Paid ${formatDate(order.paidAt)}`
                : "Awaiting Payment"}
            </span>
            <span style={styles.statusBadge(order.isPaid, order.isDelivered)}>
              {order.isDelivered ? (
                <FiCheckCircle size={14} />
              ) : (
                <FiTruck size={14} />
              )}
              {order.isDelivered
                ? `Delivered ${formatDate(order.deliveredAt)}`
                : "Pending Delivery"}
            </span>
          </div>
        </header>

        {/* Main Grid */}
        <div style={styles.grid} className="order-grid">
          {/* Left Column */}
          <div style={styles.mainContent}>
            {/* Shipping Info */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <div
                  style={{
                    ...styles.cardIcon,
                    background: "#dbeafe",
                    color: "#2563eb",
                  }}
                >
                  <FiTruck />
                </div>
                <h2 style={styles.cardTitle}>Shipping Information</h2>
                {!order.isPaid && !editingAddress && (
                  <button
                    style={styles.editBtn}
                    onClick={() => setEditingAddress(true)}
                  >
                    <FiEdit3 size={14} /> Edit
                  </button>
                )}
                {!order.isPaid && editingAddress && (
                  <button
                    style={{
                      ...styles.editBtn,
                      color: "#16a34a",
                      borderColor: "#bbf7d0",
                    }}
                    onClick={saveAddress}
                    disabled={loadingUpdate}
                  >
                    <FiSave size={14} /> {loadingUpdate ? "Saving..." : "Save"}
                  </button>
                )}
              </div>
              <div style={styles.cardBody}>
                <div style={styles.infoGrid}>
                  <div style={styles.infoItem}>
                    <div style={styles.infoIcon}>
                      <FiUser size={16} />
                    </div>
                    <div>
                      <p style={styles.infoLabel}>Customer</p>
                      <p style={styles.infoValue}>{order.user.name}</p>
                    </div>
                  </div>
                  <div style={styles.infoItem}>
                    <div style={styles.infoIcon}>
                      <FiMail size={16} />
                    </div>
                    <div>
                      <p style={styles.infoLabel}>Email</p>
                      <a
                        href={`mailto:${order.user.email}`}
                        style={{
                          ...styles.infoValue,
                          color: "#3b82f6",
                          textDecoration: "none",
                        }}
                      >
                        {order.user.email}
                      </a>
                    </div>
                  </div>
                </div>

                {/* Editable address form */}
                {!order.isPaid && editingAddress ? (
                  <div
                    style={{
                      ...styles.addressBox,
                      background: "var(--bg-surface)",
                      border: "1px solid var(--border-color)",
                    }}
                  >
                    <div style={{ marginBottom: "8px" }}>
                      <label style={styles.formLabel}>Address</label>
                      <input
                        type="text"
                        style={styles.formInput}
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                        placeholder="Enter address"
                      />
                    </div>
                    <div style={styles.formRow}>
                      <div>
                        <label style={styles.formLabel}>City</label>
                        <input
                          type="text"
                          style={styles.formInput}
                          value={city}
                          onChange={(e) => setCity(e.target.value)}
                          placeholder="Enter city"
                        />
                      </div>
                      <div>
                        <label style={styles.formLabel}>Postal Code</label>
                        <input
                          type="text"
                          style={styles.formInput}
                          value={postalCode}
                          onChange={(e) => setPostalCode(e.target.value)}
                          placeholder="Enter postal code"
                        />
                      </div>
                    </div>
                    <div style={{ maxWidth: "50%" }}>
                      <label style={styles.formLabel}>Country</label>
                      <input
                        type="text"
                        style={styles.formInput}
                        value={country}
                        onChange={(e) => setCountry(e.target.value)}
                        placeholder="Enter country"
                      />
                    </div>
                  </div>
                ) : (
                  <div style={styles.addressBox}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "12px",
                      }}
                    >
                      <FiMapPin
                        style={{ color: "#64748b", marginTop: "2px" }}
                      />
                      <p style={styles.addressText}>
                        {order.shippingAddress.address}
                        <br />
                        {order.shippingAddress.city},{" "}
                        {order.shippingAddress.postalCode}
                        <br />
                        {order.shippingAddress.country}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Payment Method */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <div
                  style={{
                    ...styles.cardIcon,
                    background: "#fef3c7",
                    color: "#d97706",
                  }}
                >
                  <FiCreditCard />
                </div>
                <h2 style={styles.cardTitle}>Payment Method</h2>
              </div>
              <div style={styles.cardBody}>
                {!order.isPaid ? (
                  <div style={styles.radioGroup}>
                    <div
                      style={styles.radioOption(
                        order.paymentMethod === "PayPal",
                      )}
                      onClick={() => handlePaymentMethodChange("PayPal")}
                    >
                      <div
                        style={styles.radioCircle(
                          order.paymentMethod === "PayPal",
                        )}
                      />
                      <span style={styles.radioLabel}>
                        PayPal or Credit Card
                      </span>
                    </div>
                    <div
                      style={styles.radioOption(
                        order.paymentMethod === "Stripe",
                      )}
                      onClick={() => handlePaymentMethodChange("Stripe")}
                    >
                      <div
                        style={styles.radioCircle(
                          order.paymentMethod === "Stripe",
                        )}
                      />
                      <span style={styles.radioLabel}>
                        Stripe (Credit / Debit Card)
                      </span>
                    </div>
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "12px",
                    }}
                  >
                    <div
                      style={{
                        padding: "12px 20px",
                        background: "#f8fafc",
                        borderRadius: "10px",
                        border: "1px solid #e2e8f0",
                      }}
                    >
                      <span style={{ fontWeight: "500", color: "#1e293b" }}>
                        {order.paymentMethod}
                      </span>
                    </div>
                    <span
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        color: "#16a34a",
                        fontSize: "14px",
                        fontWeight: "500",
                      }}
                    >
                      <FiCheckCircle /> Verified
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Order Items */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <div
                  style={{
                    ...styles.cardIcon,
                    background: "#f0fdf4",
                    color: "#16a34a",
                  }}
                >
                  <FiShoppingBag />
                </div>
                <h2 style={styles.cardTitle}>
                  Order Items ({order.orderItems.length})
                </h2>
              </div>
              <div style={styles.cardBody}>
                {order.orderItems.map((item, index) => (
                  <div
                    key={index}
                    style={{
                      ...styles.orderItem,
                      borderBottom:
                        index === order.orderItems.length - 1
                          ? "none"
                          : "1px solid #f1f5f9",
                    }}
                  >
                    <img
                      src={item.image}
                      alt={item.name}
                      style={styles.itemImage}
                    />
                    <div style={styles.itemDetails}>
                      <Link
                        to={`/product/${item.product}`}
                        style={styles.itemName}
                      >
                        {item.name}
                      </Link>
                      <span style={styles.itemMeta}>Qty: {item.qty}</span>
                    </div>
                    <div style={styles.itemPrice}>
                      <span style={styles.priceMain}>
                        ${(item.qty * item.price).toFixed(2)}
                      </span>
                      <span style={styles.priceCalc}>
                        ${item.price.toFixed(2)} each
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Sidebar */}
          <div style={styles.sidebar}>
            {/* Order Summary */}
            <div style={styles.summaryCard}>
              <h3 style={styles.summaryTitle}>
                <FiPackage />
                Order Summary
              </h3>
              <div style={styles.summaryRow}>
                <span style={styles.summaryLabel}>Subtotal</span>
                <span style={styles.summaryValue}>${order.itemsPrice}</span>
              </div>
              <div style={styles.summaryRow}>
                <span style={styles.summaryLabel}>Shipping</span>
                <span style={styles.summaryValue}>
                  {parseFloat(order.shippingPrice) === 0
                    ? "Free"
                    : `$${order.shippingPrice}`}
                </span>
              </div>
              <div style={styles.summaryRow}>
                <span style={styles.summaryLabel}>Tax</span>
                <span style={styles.summaryValue}>${order.taxPrice}</span>
              </div>
              <div style={styles.summaryTotal}>
                <span>Total</span>
                <span>${order.totalPrice}</span>
              </div>
            </div>

            {/* Payment Section */}
            {!order.isPaid && (
              <div style={styles.paymentCard}>
                <h4 style={styles.paymentTitle}>
                  <FiCreditCard />
                  Complete Payment
                </h4>
                {loadingPay && (
                  <div style={{ textAlign: "center", padding: "20px" }}>
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">Processing...</span>
                    </div>
                  </div>
                )}

                {/* ── Stripe ── */}
                {order.paymentMethod === "Stripe" ? (
                  <StripePaymentWrapper
                    orderId={orderId}
                    onSuccess={(details) => {
                      payOrder(
                        { orderId, details },
                        {
                          onSuccess: () => {
                            refetch();
                          },
                          onError: () => {},
                        },
                      );
                    }}
                  />
                ) : /* ── PayPal ── */
                isPending ? (
                  <>
                    <div style={{ textAlign: "center", padding: "20px" }}>
                      <div
                        className="spinner-border text-primary"
                        role="status"
                      >
                        <span className="visually-hidden">
                          Loading PayPal...
                        </span>
                      </div>
                      <p
                        style={{
                          marginTop: "12px",
                          fontSize: "13px",
                          color: "#64748b",
                        }}
                      >
                        PayPal is loading...
                      </p>
                    </div>
                    {/* Test payment button for development */}
                    <button
                      type="button"
                      onClick={() => {
                        if (
                          window.confirm("Use test payment? (Development only)")
                        ) {
                          payOrder(
                            {
                              orderId,
                              details: {
                                id: `TEST-${Date.now()}`,
                                status: "COMPLETED",
                                update_time: new Date().toISOString(),
                                source: "test",
                              },
                            },
                            {
                              onSuccess: () => {
                                refetch();
                              },
                              onError: () => {},
                            },
                          );
                        }
                      }}
                      style={{
                        width: "100%",
                        padding: "12px",
                        background: "#f59e0b",
                        color: "#fff",
                        border: "none",
                        borderRadius: "8px",
                        fontSize: "14px",
                        fontWeight: "500",
                        cursor: "pointer",
                        marginTop: "8px",
                      }}
                    >
                      Use Test Payment (Dev)
                    </button>
                  </>
                ) : (
                  <>
                    <PayPalButtons
                      createOrder={createOrder}
                      onApprove={onApprove}
                      onError={onError}
                      style={{ layout: "vertical" }}
                    />
                    {/* Fallback test payment button */}
                    <button
                      type="button"
                      onClick={() => {
                        if (
                          window.confirm(
                            "Skip PayPal and use test payment? (Development only)",
                          )
                        ) {
                          payOrder(
                            {
                              orderId,
                              details: {
                                id: `TEST-${Date.now()}`,
                                status: "COMPLETED",
                                update_time: new Date().toISOString(),
                                source: "test",
                              },
                            },
                            {
                              onSuccess: () => {
                                refetch();
                              },
                              onError: () => {},
                            },
                          );
                        }
                      }}
                      style={{
                        width: "100%",
                        padding: "10px",
                        background: "transparent",
                        color: "#f59e0b",
                        border: "1px solid #f59e0b",
                        borderRadius: "8px",
                        fontSize: "13px",
                        fontWeight: "500",
                        cursor: "pointer",
                        marginTop: "12px",
                      }}
                    >
                      Use Test Payment Instead
                    </button>
                  </>
                )}
              </div>
            )}

            {/* Admin Deliver Button */}
            {userInfo &&
              userInfo.isAdmin &&
              order.isPaid &&
              !order.isDelivered && (
                <button
                  style={styles.adminBtn}
                  onClick={deliverHandler}
                  disabled={loadingDeliver}
                >
                  {loadingDeliver ? (
                    <>
                      <span
                        className="spinner-border spinner-border-sm"
                        role="status"
                      />
                      Processing...
                    </>
                  ) : (
                    <>
                      <FiTruck />
                      Mark as Delivered
                    </>
                  )}
                </button>
              )}

            {/* Order Paid Success */}
            {order.isPaid && (
              <div
                style={{
                  background: "#f0fdf4",
                  border: "1px solid #bbf7d0",
                  borderRadius: "12px",
                  padding: "16px",
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                }}
              >
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "50%",
                    background: "#dcfce7",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#16a34a",
                  }}
                >
                  <FiCheckCircle size={20} />
                </div>
                <div>
                  <p
                    style={{
                      margin: 0,
                      fontWeight: "600",
                      color: "#166534",
                      fontSize: "14px",
                    }}
                  >
                    Payment Successful
                  </p>
                  <p
                    style={{
                      margin: 0,
                      color: "#15803d",
                      fontSize: "12px",
                    }}
                  >
                    {formatDate(order.paidAt)}
                  </p>
                </div>
              </div>
            )}

            {/* Delivered Success */}
            {order.isDelivered && (
              <div
                style={{
                  background: "#eff6ff",
                  border: "1px solid #bfdbfe",
                  borderRadius: "12px",
                  padding: "16px",
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                }}
              >
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "50%",
                    background: "#dbeafe",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#2563eb",
                  }}
                >
                  <FiTruck size={20} />
                </div>
                <div>
                  <p
                    style={{
                      margin: 0,
                      fontWeight: "600",
                      color: "#1e40af",
                      fontSize: "14px",
                    }}
                  >
                    Order Delivered
                  </p>
                  <p
                    style={{
                      margin: 0,
                      color: "#3b82f6",
                      fontSize: "12px",
                    }}
                  >
                    {formatDate(order.deliveredAt)}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default OrderScreen;
