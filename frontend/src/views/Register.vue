<template>
  <div class="container vh-90 d-flex justify-content-center align-items-center ff">
    <div class="card p-4 shadow" style="width: 400px;">

      <h4 class="text-center text-dark mb-3">Patient Registration</h4>
      <p class="text-center text-muted small mb-4">
          Create your account to book appointments
        </p>

      <form @submit.prevent="register">
      
      <div class="mb-1">
        <label class="form-label fw-semibold">Full Name</label>
        <input v-model="name" type="text" class="form-control mb-1 input-soft border" placeholder="Enter your Full Name" required/>
      </div>
      
      <div class="mb-1">
        <label class="form-label fw-semibold">Email</label>
        <input v-model="email" type="email" class="form-control mb-1 input-soft border" placeholder="Email" required />
      </div>

      
      <div class="mb-1">
          <label class="form-label fw-semibold">Password</label>
        <input v-model="password" type="password" class="form-control mb-1 input-soft border" placeholder="Password" required />
      </div>

      <div class="mb-1">
        <label class="form-label fw-semibold">Phone Number</label>
        <input v-model="phone" type="text" class="form-control mb-1 input-soft border" placeholder="Phone" required />
      </div>

      <div class="row">
          <div class="col-6 mb-1">
        <label class="form-label fw-semibold">Age</label>
        <input v-model="age" type="text" class="form-control mb-1 input-soft border" placeholder="Age" required />
        <p v-if="ageError" class="text-danger">{{ ageError }}</p>
      </div>

      <div class="col-6 mb-1">
            <label class="form-label fw-semibold" >Gender</label>
        <select v-model="gender" class="form-control mb-1 input-soft border" required>
          <option value="">Select</option>
          <option>Male</option>
          <option>Female</option>
          <option>Other</option>
        </select>
      </div>
        </div>

        <button class="btn btn-dark w-100 mt-3">Register</button>
      </form>

      <p class="text-danger text-center mt-1">{{ error }}</p>

      <div class="text-center ">
      <p class="text-center small">
       Already have an account?
        <router-link to="/" class="text-primary fw-semibold text-decoration-none">Sign in</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/services/interceptor"

export default {
  data() {
    return {
      name: "",
      email: "",
      phone: "",
      age: "",
      gender: "",
      password: "",
      error: ""
    }
  },
  methods: {
    onlyNumbers(event) {
    if (!/[0-9]/.test(event.key)) {
      event.preventDefault();
    }
  },
    register() {
      api.post(
        "/auth/register",
        {
          name: this.name,
          email: this.email,
          phone: this.phone,
          age: this.age,
          gender: this.gender,
          password: this.password
        },
        {
          headers: { "Content-Type": "application/json" }
        }
      )
      .then(() => {
        alert("Registered successfully")
        this.$router.push("/")
      })
      .catch(err => {
        this.error = err.response?.data?.message || "Registration failed"
      })
    }
  }
}
</script>

<style  scoped>
.ff{
  font-family: 'Poppins', sans-serif;
}
.input-soft {
  background-color: #f3f4f6;
  border: none;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
}

.form-control:focus {
  border-color: #9ca3af;
  box-shadow: 0 0 0 2px rgba(156, 163, 175, 0.2);
}
input:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 1000px #eeefef inset !important;
  -webkit-text-fill-color: #000 !important;
}
</style> 
this is my current app.py register : @auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json

    name = data.get("name")
    email = data.get("email", "").strip().lower()
    phone = data.get("phone")
    age = data.get("age")
    gender = data.get("gender")
    password = data.get("password")

    if not all([name, email, password]):
        return jsonify({"message": "All required fields are mandatory"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Email already registered"}), 400

    hashed_password = generate_password_hash(password)

    new_user = User(
        name=name,
        email=email,
        phone=phone,
        age=age,
        gender=gender,
        password=hashed_password,
        role="patient"
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Patient registered successfully"}), 201