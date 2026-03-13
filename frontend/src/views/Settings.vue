<template>
  <div class="settings-page">

    <h1 class="main-title">Reminder Settings</h1>

    <!-- DAILY REMINDER -->
    <div class="reminder-box">

      <div class="box-header">
        <h2 class="box-title">Daily Reminder</h2>

        <label class="switch">
          <input type="checkbox" v-model="dailyToggle">
          <span class="slider"></span>
        </label>
      </div>

      <div v-if="dailyToggle" class="box-body">
        <input type="time">
        <button class="send-btn">Send</button>
      </div>

    </div>


    <!-- MONTHLY REMINDER -->
    <div class="reminder-box">

      <div class="box-header">
        <h2 class="box-title">Monthly Reminder</h2>

        <label class="switch">
          <input type="checkbox" v-model="monthlyToggle">
          <span class="slider"></span>
        </label>
      </div>

      <div v-if="monthlyToggle" class="box-body">
        <input type="date">
        <button class="send-btn">Send</button>
      </div>

    </div>

  </div>
</template>

<script>
export default {
  data(){
    return{
      dailyToggle:false,
      monthlyToggle:false
    }
  }
}
</script>

<style>

.settings-page{
padding:40px;
width:100%;
}

/* Main title */

.main-title{
font-size:28px;
margin-bottom:30px;
font-weight:600;
}

/* Reminder boxes */

.reminder-box{
background:white;
border-radius:12px;
padding:30px;
margin-bottom:25px;
width:100%;
box-shadow:0 4px 10px rgba(0,0,0,0.08);
}

/* Header */

.box-header{
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:20px;
border-bottom:1px solid #eee;
padding-bottom:10px;
}

/* Reduce font */

.box-title{
font-size:20px;
font-weight:500;
}

/* Body */

.box-body{
display:flex;
gap:12px;
margin-top:15px;
}

/* Inputs */

input{
padding:10px;
border-radius:6px;
border:1px solid #ccc;
}

/* Button */

.send-btn{
background:#3b82f6;
color:white;
border:none;
padding:10px 18px;
border-radius:6px;
cursor:pointer;
}

/* Toggle */

.switch{
position:relative;
display:inline-block;
width:45px;
height:22px;
}

.switch input{
display:none;
}

.slider{
position:absolute;
background:#ccc;
border-radius:20px;
top:0;
left:0;
right:0;
bottom:0;
}

.slider:before{
content:"";
position:absolute;
height:18px;
width:18px;
left:2px;
bottom:2px;
background:white;
border-radius:50%;
transition:0.3s;
}

input:checked + .slider{
background:#3b82f6;
}

input:checked + .slider:before{
transform:translateX(22px);
}

</style>