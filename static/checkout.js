// This is your test secret API key.
const stripe = Stripe("pk_test_51RofqsRxn8ni2a1RHnIhU9K5BGbvGL9mwtFfEb2jGhnWxjJ57l6Uf8Na6Pc199LQZAk0UdaCcKNM4eP8g5d2p9k300txchwFlQ");

initialize();

// Create a Checkout Session
async function initialize() {
  const fetchClientSecret = async () => {
    const response = await fetch("/create-checkout-session", {
      method: "POST",
    });
    const { clientSecret } = await response.json();
    return clientSecret;
  };

  const checkout = await stripe.initEmbeddedCheckout({
    fetchClientSecret,
  });

  // Mount Checkout
  checkout.mount('#checkout');
}