<script>
export default {
    data: () => ({
        step: 1,
        data_path: '',

        retail_searching: false,
        retail_found: false,
        retail_path: '',
        retail_installed: false,

        installer_path: '',

        wl_popup_visible: false,

        neb_user: '',
        neb_password: '',
        neb_email: ''
    }),

    created() {
        this.retail_searching = true;
        this.retail_found = false;

        call(fs2mod.searchRetailData, (path) => {
            this.retail_searching = false;

            if(path !== '') {
                this.retail_found = true;
                this.retail_path = path;
            }
        });

        call(fs2mod.getDefaultBasePath, (result) => {
            this.data_path = result;
        });
    },

    methods: {
        selectDataFolder() {
            call(fs2mod.browseFolder, 'Please select a folder', this.data_path, (path) => {
                if(path) this.data_path = path;
            });
        },

        finishFirst() {
            call(fs2mod.setBasePath, this.data_path, (result) => {
                if(result) {
                    this.step++;
                }
            });
        },

        selectInstaller() {
            call(fs2mod.browseFiles, 'Please select your setup_freespace2_...exe', this.installer_path, '*.exe', (files) => {
                if(files.length > 0) {
                    this.installer_path = files[0];
                }
            });
        },

        selectRetailFolder() {
            call(fs2mod.browseFolder, 'Please select your FS2 folder', this.retail_path, (path) => {
                if(path) this.retail_path = path;
            });
        },

        processRetail() {
            let path = this.installer_path === '' ? this.retail_path : this.installer_path;
            call(fs2mod.copyRetailData, path, (result) => {
                if(result) {
                    vm.popup_visible = true;
                    vm.popup_title = 'Installing Retail';
                    vm.popup_mode = 'mod_progress';
                    vm.popup_mod_id = 'FS2';

                    connectOnce(fs2mod.retailInstalled, () => {
                        vm.popup_visible = false;
                        this.retail_installed = true;
                        this.step++;
                    });
                }
            });
        },

        skipRetail() {
            this.wl_popup_visible = false;
            this.step++;
        },
        
        login() {
            fs2mod.nebLogin(this.neb_user, this.neb_password);
        },

        register() {
            if(this.neb_user == '' || this.neb_password == '' || this.neb_email == '') {
                alert('You have to enter your desired username, password and email address!');
            } else {
                fs2mod.nebRegister(this.neb_user, this.neb_password, this.neb_email);
            }
        },

        resetPassword() {
            fs2mod.nebResetPassword(this.neb_user);
        },

        goToExplore() {
            vm.showTab('explore');
        },

        goToMVPS() {
            vm.page = 'details';
            vm.mod = mod_table.MVPS;
        }
    }
};
</script>
<template>
    <div class="container main-notice">
        <div v-if="step === 1">
            <h1>Welcome!</h1>
            
            <p>It looks like you started Knossos for the first time.</p>
            <p>You need to select a directory where Knossos will store the game data (models, textures, etc.).</p>
            
            <p>We recommend...</p>
            <form class="form-horizontal">
                <div class="input-group">
                    <input type="text" class="form-control" v-model="data_path">
                    <span class="input-group-btn">
                        <button class="btn btn-default" @click.prevent="selectDataFolder">Browse...</button>
                    </span>
                </div>
                <br>
            </form>
            
            <p>
                <button v-if="retail_searching" class="btn btn-primary" disabled>Please wait...</button>
                <button v-else class="btn btn-primary" @click.prevent="finishFirst">Continue</button>
            </p>
        </div>

        <div v-else-if="step === 2">
            <h1>Great!</h1>

            <form class="form-horizontal">
                <p>Just a few more steps...</p>

                <div v-if="retail_found">
                    <p>We found an existing Freespace 2 installation in the location below. Is this correct?</p>

                    <p><strong>{{ retail_path }}</strong></p>

                    <p>
                        <button class="btn btn-primary" @click.prevent="processRetail">Yes</button>
                        <button class="btn btn-default pull-right" @click.prevent="retail_found = false">No</button>
                    </p>
                </div>
                <div v-else>
                    <p>
                        If you want to play Freespace 2 Mods (Games that are built on and modify Retail Freespace 2 data), you'll need
                        to get Retail Freespace 2 installed. First, you'll need to own a copy. You can buy it here at
                        <a href="https://www.gog.com/game/freespace_2" class="open-ext">gog.com</a> for just a few dollars.
                    </p>

                    <p>Once you have purchased Freespace 2, just point us to the GOG Installer EXE you downloaded.</p>
                
                    <div class="input-group">
                        <input type="text" class="form-control" v-model="installer_path">
                        <span class="input-group-btn">
                            <button class="btn btn-default" @click.prevent="selectInstaller">Browse...</button>
                        </span>
                    </div>
                    <br>

                    <p>OR...</p>

                    <p>If you already own Freespace 2, just point us to the retail data files (usually C:\Games\Freespace2).</p>

                    <div class="input-group">
                        <input type="text" class="form-control" v-model="retail_path">
                        <span class="input-group-btn">
                            <button class="btn btn-default" @click.prevent="selectRetailFolder">Browse...</button>
                        </span>
                    </div>
                    <br>

                    <p>
                        <button class="btn btn-primary" @click.prevent="processRetail">Continue</button>
                        <button class="btn btn-default pull-right" @click.prevent="wl_popup_visible = true">Skip</button>
                    </p>
                </div>
            </form>
        </div>

        <div v-else-if="step === 3">
            <h1>Suit Up, Pilot!</h1>

            <p>
                Everything's setup and you can start playing Freespace Open games right away. Head on over to the
                <a href="#" @click.prevent="goToExplore">Explore</a> tab and pick a few to start with.
            </p>

            <p v-if="retail_installed">
                If you are interested in playing Retail Freespace 2, we recommend you install the
                <a href="#" @click.prevent="goToMVPS">MediaVPs mod</a>. That mod will let you play Freespace 2 with all
                of the glittery graphical goodness that Hard-Light has created over the years!
            </p>

            <p><button class="btn btn-primary" @click.prevent="goToExplore">Finish</button></p>

            <hr>

                <div class="welcome-login">
                    Are you a mod developer? Login!
                    <div class="login-form">
                        <div class="form-group">
                            <label class="col-sm-4 welcome-label">Username:</label>
                            <div class="col-sm-8">
                                <input type="text" class="neb-input" v-model="neb_user">
                            </div>
                        </div>

                        <br>

                        <div class="form-group">
                            <label class="col-sm-4 welcome-label">Password:</label>
                            <div class="col-sm-8">
                                <input type="password" class="neb-input" v-model="neb_password">
                            </div>
                        </div>

                        <br>

                        <div class="form-group">
                            <label class="col-sm-4 welcome-label">E-Mail:</label>
                            <div class="col-sm-8">
                                <input type="email" class="neb-input" v-model="neb_email" placeholder="only required for registration">
                            </div>
                        </div>

                        <br>

                        <div class="form-group">
                            <div class="col-sm-offset-2 col-sm-8 neb-btns">
                                <button class="mod-btn btn-link-blue" @click="login">Login</button>
                                <button class="mod-btn btn-link-blue" @click="register">Register</button>
                                <button class="mod-btn btn-link-red" @click="resetPassword">Reset Pass</button>
                            </div>
                        </div>
                    </div>
                </div>
        </div>

        <div v-else>
            <h1>Whoops</h1>

            <p>You somehow managed to end up in nirvana. If you see this page, please tell us how you managed that!</p>
        </div>

        <hr>

        <p>
            This launcher is still in development. Join us on
            <a href="https://discord.gg/qfReB8t" class="open-ext">#knossos</a>
            in HLP's Discord or visit our
            <a href="https://www.hard-light.net/forums/index.php?topic=94068.0" class="open-ext">release thread</a>
            and let us know what you think, what didn't work and what you would like to change.
        </p>
        <p>-- ngld</p>

        <div class="popup-bg" v-if="wl_popup_visible" @click.prevent="wl_popup_visible = false"></div>

        <div class="popup" v-if="wl_popup_visible">
            <div class="title clearfix">
                Are You Sure?

                <a href="" class="pull-right" @click.prevent="wl_popup_visible = false">
                    <i class="fa fa-times"></i>
                </a>
            </div>
            <div class="content gen-scroll-style">
                <p>
                    You can skip this step, but you won't be able to play most games that Knossos offers.
                    If you try to install a Freespace2 mod, you'll be asked to install Retail Freespace2 again.
                </p>

                <p>You can always install Retail Freespace2 from the settings!</p>

                <div class="popup-buttons">
                    <button class="btn btn-default" @click.prevent="skipRetail">Skip</button>
                    <button class="btn btn-default pull-right" @click.prevent="wl_popup_visible = false">Cancel</button>
                </div>
            </div>
        </div>
    </div>
</template>